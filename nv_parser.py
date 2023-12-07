from xml.etree.ElementTree import fromstring


def parse_nvidia_smi(gpu_state_str):

    xml = fromstring(gpu_state_str)
    num_gpus = int(list(xml.iter('attached_gpus'))[0].text)
    # print(num_gpus)
    results = []
    for gpu_id, gpu in enumerate(xml.iter('gpu')):
        gpu_data = {}

        name = list(gpu.iter('product_name'))[0].text
        gpu_data['name'] = name

        # get memory
        memory_usage = list(gpu.iter('fb_memory_usage'))[0]
        total_memory = list(memory_usage.iter('total'))[0].text
        used_memory = list(memory_usage.iter('used'))[0].text
        free_memory = list(memory_usage.iter('free'))[0].text
        gpu_data['memory'] = {
            'total': total_memory,
            'used_memory': used_memory,
            'free_memory': free_memory
        }

        # get utilization
        utilization = list(gpu.iter('utilization'))[0]
        gpu_util = list(utilization.iter('gpu_util'))[0].text
        memory_util = list(utilization.iter('memory_util'))[0].text
        gpu_data['utilization'] = {
            'gpu_util': gpu_util,
            'memory_util': memory_util
        }

        # processes
        processes = list(gpu.iter('processes'))[0]
        infos = []
        for info in list(processes.iter('process_info')):
            pid = list(info.iter('pid'))[0].text
            process_name = list(info.iter('process_name'))[0].text
            used_memory = list(info.iter('used_memory'))[0].text
            infos.append({
                'pid': pid,
                'process_name': process_name,
                'used_memory': used_memory
            })
        gpu_data['processes'] = infos

        results.append(gpu_data)
    return results

