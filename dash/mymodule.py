import json

def handler(input: dict, context: object) -> dict:
    env = context.env or {}
    moving_avg_cpu = env.get('moving_avg_cpu', {})
    num_cpus = sum(1 for k in input.keys() if k.startswith("cpu_percent-"))
    bytes_sent = input.get("net_io_counters_eth0-bytes_sent1", 0)
    bytes_recv = input.get("net_io_counters_eth0-bytes_recv1", 1)
    percent_network_egress = (bytes_sent / (bytes_sent + bytes_recv)) * 100
    cached = input.get("virtual_memory-cached", 0)
    buffers = input.get("virtual_memory-buffers", 0)
    total_memory = input.get("virtual_memory-total", 1)
    percent_memory_caching = ((cached + buffers) / total_memory) * 100

    for i in range(num_cpus):
        key = f"cpu_percent-{i}"
        cpu_util = input.get(key, 0)
        prev_avg = moving_avg_cpu.get(key, 0)
        moving_avg_cpu[key] = (prev_avg * 59 + cpu_util) / 60

    env['moving_avg_cpu'] = moving_avg_cpu

    result = {
        "percent-network-egress": percent_network_egress,
        "percent-memory-caching": percent_memory_caching,
    }
    result.update({f"avg-util-cpu{i}-60sec": moving_avg_cpu[f"cpu_percent-{i}"] for i in range(num_cpus)})
    return result
