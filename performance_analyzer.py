import psutil
import time

_start_time = time.time()

def get_performance_report():
    """
    Tracks runtime memory usage, CPU utilization, and system uptime.
    """
    process = psutil.Process()
    ram_usage_mb = process.memory_info().rss / (1024 * 1024)
    uptime_sec = time.time() - _start_time
    
    return {
        "RAM Usage (MB)": round(ram_usage_mb, 2),
        "Uptime (seconds)": round(uptime_sec, 2),
        "CPU Utilization (%)": psutil.cpu_percent(interval=None)
    }
