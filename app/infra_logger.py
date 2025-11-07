import logging
import os
import psutil
import socket

try:
    from newrelic.agent import NewRelicContextFormatter
    formatter = NewRelicContextFormatter()
except ImportError:
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

infra_logger = logging.getLogger('infrastructure')
infra_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
infra_logger.addHandler(handler)

def log_infra_event(event_type, message, level='info', **kwargs):
    """インフライベントをログ出力"""
    log_data = {
        'event_type': event_type,
        'hostname': socket.gethostname(),
        'container_id': os.getenv('HOSTNAME', 'unknown'),
        **kwargs
    }
    log_msg = f"[INFRA] {message} | {log_data}"
    
    if level == 'error':
        infra_logger.error(log_msg)
    elif level == 'warning':
        infra_logger.warning(log_msg)
    else:
        infra_logger.info(log_msg)

def log_system_resources():
    """システムリソース状態をログ出力"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        log_infra_event(
            'system_resources',
            f'CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%',
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / 1024 / 1024,
            disk_percent=disk.percent
        )
    except Exception as e:
        log_infra_event('system_resources_error', f'Failed to collect system resources: {e}', level='error')
