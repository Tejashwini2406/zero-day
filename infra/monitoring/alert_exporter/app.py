from prometheus_client import Gauge, start_http_server
import time
import os

WINDOWS_DIR = os.environ.get('WINDOWS_DIR', '/data/graphs')
PROCESSED_DIR = os.environ.get('PROCESSED_DIR', '/data/processed')

g_windows = Gauge('zd_windows_count', 'Number of parquet window files present')
g_alerts = Gauge('zd_alerts_count', 'Number of alert json files present')

def count_files(path, suffixes):
    try:
        names = os.listdir(path)
    except Exception:
        return 0
    return sum(1 for n in names if any(n.endswith(s) for s in suffixes))

def run():
    start_http_server(8000)
    while True:
        windows = count_files(WINDOWS_DIR, ['.parquet'])
        alerts = count_files(PROCESSED_DIR, ['.alert.json', '.xai.json'])
        g_windows.set(windows)
        g_alerts.set(alerts)
        time.sleep(5)

if __name__ == '__main__':
    run()
from prometheus_client import start_http_server, Gauge, Counter
import time
import os
import glob

ALERT_DIR = os.environ.get('ALERT_DIR', '/data/processed')
GRAPH_DIR = os.environ.get('GRAPH_DIR', '/data/graphs')
PORT = int(os.environ.get('PORT', '9417'))

alerts_gauge = Gauge('zero_day_alerts_total', 'Number of alert files observed')
windows_gauge = Gauge('zero_day_windows_total', 'Number of graph windows observed')
latest_window_ts = Gauge('zero_day_latest_window_ts', 'Latest window timestamp')

def scan():
    # count alert json files
    alerts = glob.glob(os.path.join(ALERT_DIR, '*.alert.json'))
    windows = glob.glob(os.path.join(GRAPH_DIR, '*.nodes.parquet'))
    alerts_gauge.set(len(alerts))
    windows_gauge.set(len(windows))
    # attempt to extract latest window timestamp from filename
    latest = 0
    for w in windows:
        name = os.path.basename(w)
        try:
            ts = int(name.split('.')[0].split('_')[-1])
            if ts > latest:
                latest = ts
        except Exception:
            continue
    latest_window_ts.set(latest)

if __name__ == '__main__':
    start_http_server(PORT)
    while True:
        scan()
        time.sleep(5)
