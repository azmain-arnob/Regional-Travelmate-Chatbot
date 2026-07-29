import psutil
import time

_start_time = time.time()

def get_performance_report():
    """Tracks RAM, CPU, and uptime. Returns a markdown string for gr.Markdown."""
    process = psutil.Process()
    ram_usage_mb = process.memory_info().rss / (1024 * 1024)
    uptime_sec = time.time() - _start_time
    return (
        "### System Performance\n"
        f"- **RAM Usage:** {round(ram_usage_mb, 2)} MB\n"
        f"- **Uptime:** {round(uptime_sec, 2)} seconds\n"
        f"- **CPU Utilization:** {psutil.cpu_percent(interval=None)} %\n"
    )
