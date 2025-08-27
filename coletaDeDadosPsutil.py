import psutil as ps
import pandas as pd
import datetime as dt
import time
import socket
import os

while(True):
mem = ps.virtual_memory()
disk = ps.disk_usage("/")
date = dt.datetime.now();
data = {
"user": socket.gethostname(),
"timestamp": str(date),
"cpu": [round((100 - ps.cpu_times_percent(interval=1,percpu=False).idle),2)],
"ram": mem.used / 1024 / 1024,
"disco": (round((disk.used/disk.total*100), 2)),
}
print(data)
df = pd.DataFrame(data)
if(os.path.exists('daniel.csv')):
df.to_csv("daniel.csv", mode="a", encoding="utf-8", index=False, sep=";", header=False)
else:
df.to_csv("daniel.csv", mode="a", encoding="utf-8", index=False, sep=";")
firstTime = False
time.sleep(1)
