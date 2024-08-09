from datetime import datetime

def format_datetime(dt: datetime) -> str:
    if dt:
        return dt.strftime('%Y-%m-%dT%H:%M:%S')
    return None