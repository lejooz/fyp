import sys
import os
import platform
import subprocess
import time
import mailer
import datetime
import config
import logging

from urllib.request import urlopen  # Python 3 fix

ip_address = None
hosts_list = {}
any_device = True
plat = platform.system()
conf = config.Configuration()
logging.basicConfig(filename='app.log', level=logging.DEBUG)

def ping(addr):
    if plat == "Windows":
        args = ["ping", "-n", "1", "-l", "1", "-w", "100", addr]
    elif plat == "Linux":
        args = ["ping", "-c", "1", "-l", "1", "-s", "1", "-W", "1", addr]
    else:
        # Default to Windows command if unknown platform
        args = ["ping", "-n", "1", "-l", "1", "-w", "100", addr]

    ping_proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, error = ping_proc.communicate()
    # Decode output from bytes to string (Python 3)
    out = out.decode('utf-8', errors='ignore')
    error = error.decode('utf-8', errors='ignore')
    if '100%' in out or '100% loss' in out or '100% packet loss' in out:
        hosts_list[addr] = False
    else:
        hosts_list[addr] = True
    print(error)

scriptDir = sys.path[0]
hosts = os.path.join(scriptDir, 'hosts.txt')
with open(hosts, "r") as hostsFile:
    lines = hostsFile.readlines()
for line in lines:
    line = line.strip()
    hosts_list[line] = False

def start_listen():
    power = False
    sub_proc = None
    global ip_address
    while True:
        now = datetime.datetime.now()
        # Check public IP on every hour and half hour
        if now.minute == 0 or now.minute == 30:
            try:
                public_ip = urlopen('http://ip.42.pl/raw').read().decode('utf-8')
                if ip_address != public_ip:
                    mailer.send_email_address(public_ip, conf)
                    logging.info('sending ip to email at ' + str(datetime.datetime.now()))
                    ip_address = public_ip
            except Exception as e:
                logging.warning(f"Could not get public IP: {e}")

        for key in hosts_list.keys():
            ping(key)
            time.sleep(1)
        # any() for values in Python 3
        if any(hosts_list.values()) and power:
            logging.info('server killed at  ' + str(datetime.datetime.now()))
            if sub_proc is not None:
                sub_proc.terminate()
                sub_proc = None
            power = False
        if not any(hosts_list.values()) and not power:
            logging.info('server started at  ' + str(datetime.datetime.now()))
            sub_proc = subprocess.Popen([sys.executable, "server.py"])  # Python 3: use sys.executable for the same Python version
            power = True
        time.sleep(10)

if __name__ == "__main__":
    start_listen()