import threading
import paramiko
import os
import time
from nv_parser import parse_nvidia_smi
import datetime

class GPUStatusMonitor(object):
    def __init__(self) -> None:
        with open('server.conf', 'r') as f:
            hosts = f.readlines()
        self.node_list = []
        for i in hosts:
            if '|' in i:
                hname, pwd = i.strip().split('|')
                self.node_list.append(RemoteGPUQuery(hname, pwd))
            else:
                self.node_list.append(RemoteGPUQuery(i.strip()))
        
        self.lock = threading.Lock()
        self._thread = None
        self.cur_res = [None]*len(self.node_list)

    def stop_update_loop(self):
        print('Try to stop all the sub-threads')
        for i in self.node_list:
            i.stop_loop_update_gpu_state()
            print(f'{i}-th thread has been terminated')
        
        self.node_list.clear()
        print('Nodes have been cleaned')
        if self._thread is not None and self._thread.is_alive():
            self._thread.stop()
        self._thread = None
        print('Controller thread has been exited')

    def get_status_list(self):
        with self.lock:
            return self.cur_res
        
    def start_update_loop(self, timeout=1e-1):
        for i in self.node_list:
            i.start_loop_update_gpu_state()

        def func(obj):
            for i, node in enumerate(obj.node_list):
                res = node.get_cur_state()
                with self.lock:
                    self.cur_res[i] = res

        t1 = LoopThread(target=func, args=[self], timeout=timeout)
        self._thread = t1
        
        self._thread.start()
            


class RemoteGPUQuery(object):
    def __init__(self, hostname, passwd=None) -> None:
        
        self.host_nickname = hostname
        self.passwd = passwd
        self.ssh_client = paramiko.SSHClient()
        self.ssh_config = paramiko.SSHConfig()
        self.user_config_file = os.path.expanduser('~/.ssh/config')
        if os.path.exists(self.user_config_file):
            with open(self.user_config_file) as f:
                self.ssh_config.parse(f)

        # Set the SSH configuration options from the parsed file
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.user_config = self.ssh_config.lookup(hostname)
        self.timeout=10
        self.cur_gpu_state = None
        self.lock = threading.Lock()
        self._thread = None

    def connect(self):
        self.ssh_client.connect(hostname=self.user_config['hostname'], username=self.user_config['user'],
                                port = self.user_config['port'], timeout=self.timeout, password=self.passwd)
        
    def check_connection(self):
        if self.ssh_client.get_transport() is not None and self.ssh_client.get_transport().is_active():
            # print("Connection is active")
            return True
        else:
            return False
        
    def query_gpu_status(self, block=False):
        try:
            while True:
                if not self.check_connection():
                    self.connect()
                else:
                    break
                # import pdb;pdb.set_trace()
                if not self.check_connection() and not block:
                    raise ConnectionError()
                    # return self.user_config['hostname'], None
                time.sleep(0.01)
        except Exception as e:
            err_info = {
                'exception_type' : type(e).__name__,
                'exception_message' : str(e),
                'traceback' : e.__traceback__}  # Traceback object
            return self.host_nickname, None, err_info, datetime.datetime.now().timestamp() # return the timestamp
        # import pdb;pdb.set_trace()
        while True:
            try:
                _stdin, _stdout,_stderr = self.ssh_client.exec_command('nvidia-smi -q -x', timeout=self.timeout)

                nvidia_str = _stdout.read().decode('utf-8')
                parse_res = parse_nvidia_smi(nvidia_str)
        
                # return self.user_config['hostname'], parse_res
                return self.host_nickname, parse_res, True, datetime.datetime.now().timestamp()
            except Exception as e:
                # print(e)
                if block:
                    pass
                else:
                    err_info = {
                    'exception_type' : type(e).__name__,
                    'exception_message' : str(e),
                    'traceback' : e.__traceback__}  # Traceback object
                    # return self.user_config['hostname'], None
                    return self.host_nickname, None, err_info, datetime.datetime.now().timestamp()
                
    def get_cur_state(self):
        state = None
        with self.lock:
            state = self.cur_gpu_state
        return state
    
    def stop_loop_update_gpu_state(self):
        if self._thread is not None and self._thread.is_alive():
            self._thread.stop()
        self._thread = None
        self.ssh_client.close()

    def start_loop_update_gpu_state(self, timeout=0.1):
        def func(obj):
            res = obj.query_gpu_status()
            with self.lock:
                self.cur_gpu_state = res

        t1 = LoopThread(target=func, args=[self], timeout=timeout)
        self._thread = t1
        
        self._thread.start()

class LoopThread(threading.Thread):
    def __init__(self, target, args, timeout=1e-2, *extra_args, **kwargs):
        super(LoopThread, self).__init__(target=target, args=args, *extra_args, **kwargs)
        self._stopper = threading.Event()
        self.func = target
        self.target_args = args
        self.timeout = timeout

    def stop(self):
        self._stopper.set()

    def stopped(self):
        return self._stopper.is_set()
    
    def run(self) -> None:
        while not self.stopped(): 
            self.func(*self.target_args)
            time.sleep(self.timeout)