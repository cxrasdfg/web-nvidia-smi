import gradio as gr
import time
from utils import GPUStatusMonitor
import pandas as pd
import os 

class GradioAPP(object):
    def __init__(self, shared=False) -> None:
        self.monitor = GPUStatusMonitor()
        self.num_node = len(self.monitor.get_status_list())
        
        dataframe_list = []
        self.add_table(dataframe_list, num_tables=self.num_node)

        self.web_demo = gr.Interface(
            self.update_table,
            None,
            outputs=dataframe_list,
            description="GPU Status",
        )
        self.shared = shared

    def run(self):
        try:
            self.monitor.start_update_loop()
            self.web_demo.launch(share=self.shared, prevent_thread_lock=True)
            while 1:
                time.sleep(1e-1)

        except KeyboardInterrupt as e:
            print('Try to exit')
            self.monitor.stop_update_loop()
            # self.web_demo.server.shutdown()
            # self.web_demo.close()
            print('bye bye')
            os._exit(0)

    def update_table(self, k, v): 
        print(k,v)
        pd_list = self.get_pd()

        return pd_list
    
    def get_pd(self):
        gpu_list = self.monitor.get_status_list()
        pd_list = [None] * len(gpu_list)
        
        for idx, (smachine_res, node) in enumerate(zip(gpu_list, self.monitor.node_list)):
            if smachine_res is not None:
                machine, res, flag, timestamp = smachine_res
                print('*'*12, machine, '*'*12)
                # for sgpu in res:
                #     for k, v in sgpu.items():a
                #         print('\t', k,'==>',v)
                
                machine_list = []
                card_name_list = []
                vram_list = []
                usage_list = []
                time_list = []
                id_list = []

                if res is not None:
                    for gid, sgpu in enumerate(res):
                        gname = sgpu['name']
                        vram = sgpu['memory']
                        used_vram = vram['used_memory']
                        total_varam = vram['free_memory']
                        utilization = sgpu['utilization']
                        
                        print('\tname', '==>', gname)
                        print('\tvram', '==>', vram)
                        print('\tutilization', '==>', utilization)

                        machine_list.append(node.host_nickname)
                        card_name_list.append(gname)
                        vram_list.append(f'{used_vram}/{total_varam}' )
                        usage_list.append(utilization['gpu_util'])
                        time_list.append(timestamp)
                        id_list.append(gid)

                    pd_list[idx] = pd.DataFrame({
                            "Machine": machine_list, 
                            "Id": id_list,
                            "Card Name": card_name_list,
                            "Memory": vram_list,
                            "Usage": usage_list,
                            "Timestamp": timestamp
                        })
                else:
                    print('*'*12, node.host_nickname, '*'*12)
                    print('\tno result')
                    pd_list[idx] = pd.DataFrame({
                        "Machine": [node.host_nickname],
                        "Id": ['N/A'],
                        "Card Name": ['N/A'],
                        "Memory": ['N/A'],
                        "Usage": ['N/A'],
                        "Timestamp": ['N/A']
                    })
            else:
                print('*'*12, node.host_nickname, '*'*12)
                print('\tno result')
                pd_list[idx] = pd.DataFrame({
                    "Machine": [node.host_nickname], 
                    "Id": ['N/A'],
                    "Card Name": ['N/A'],
                    "Memory": ['N/A'],
                    "Usage": ['N/A'],
                    "Timestamp": ['N/A']
                })
                
        return pd_list
    
    def loop_run(self):
        # sg = RemoteGPUQuery('204')
        # print(sg.query_gpu_status())
        self.monitor.start_update_loop()
        try:
            while True:
                gpu_list = self.monitor.get_status_list()
                
                for smachine_res, node in zip(gpu_list, self.monitor.node_list):
                    if smachine_res is not None:
                        machine, res, flag, timestamp = smachine_res
                        print('*'*12, machine, '*'*12)
                        # for sgpu in res:
                        #     for k, v in sgpu.items():a
                        #         print('\t', k,'==>',v)
                        for sgpu in res:
                            gname = sgpu['name']
                            vram = sgpu['memory']
                            used_vram = vram['used_memory']
                            total_varam = vram['free_memory']
                            utils = sgpu['utilization']
                            
                            print('\tname', '==>', gname)
                            print('\tvram', '==>', vram)
                            print('\tutilization', '==>', utils)
                    else:
                        print('*'*12, node.host_nickname, '*'*12)
                        print('\tno result')
                        pass 
                time.sleep(2)
        except KeyboardInterrupt as e:
            self.monitor.stop_update_loop()
        

    def add_table(self, dataframe_list, num_tables):
        for i in range(num_tables):
            dataframe_list.append(
                gr.Dataframe(
                    headers=["Machine", "Id", "Card Name", "Memory", "Usage", 'Timestamp'],
                    datatype=["str", "str", "str", "str", "str", "str"],
                    row_count=1,
                    col_count=(6, "fixed"),
                ))
    


    # demo.render()
