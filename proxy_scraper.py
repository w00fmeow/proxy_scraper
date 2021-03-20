#!/usr/bin/env python3
import requests
import os
import sys
import threading
from queue import Queue
from pathlib import Path
from lxml.html import fromstring


class Scraper():
    WORKERS = 40
    LIVE_PROXIES_TRESHOLD = 50
    TIMEOUT = 2
    TIMES_TO_CHECK = 3
    LIVE_PROXIES_PATH = str(Path(os.path.realpath(
        __file__)).parents[0]) + '/live_proxies.txt'
    SOCKS5_PROXY_URL = (
        'socks5', 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=10000&country=all&ssl=all&anonymity=all')
    SOCKS4_PROXY_URL = (
        'socks4', "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=10000&country=all&ssl=all&anonymity=all")
    HTTP_PROXY_URL = (
        'http', "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=yes&anonymity=all")
    CHECKER = ('https://google.com', 'Google')

    def __init__(self):
        self.urls = [self.HTTP_PROXY_URL, self.SOCKS5_PROXY_URL]
        #  self.SOCKS4_PROXY_URL]
        self.proxy_bin = []
        self.proxy_live = []
        self.threads = []
        self.proxies_to_proccess = Queue()

    def save_proxies(self):
        print('--- Saving proxies')
        f = open(self.LIVE_PROXIES_PATH, 'w')
        for p in self.proxy_live:
            f.write(p["protocol"] + ' ' + p["host"] + ' ' + p['port'])
            f.write('\n')
        f.close()

    def get_total_live_proxies(self):
        return len(self.proxy_live)

    def dispatch_threads(self):
        for _ in range(self.WORKERS):
            t = threading.Thread(target=self.worker)
            self.threads.append(t)

        for t in self.threads:
            t.start()

        for t in self.threads:
            t.join()

    def worker(self):
        while not self.proxies_to_proccess.empty() and len(self.proxy_live) < self.LIVE_PROXIES_TRESHOLD:
            proxy = self.proxies_to_proccess.get()
            if self.check_proxy(host=proxy['host'], port=proxy['port'], protocol=proxy['protocol']):
                print('--- FOUND live proxy!')
                self.proxy_live.append(proxy)

    def load_proxies(self):
        try:
            print("--- Loading proxies")
            for protocol, url in self.urls:
                r = requests.get(url)
                self.proxy_bin = [{'host': x.split(':')[0], 'port': x.split(':')[1], 'protocol': protocol}
                                  for x in r.text.split('\r\n') if x]
                for p in self.proxy_bin:
                    self.proxies_to_proccess.put(p)

            print(f'Got {len(self.proxy_bin)} proxies')
        except Exception as e:
            # print(e)
            pass

    def check_proxy(self, host, port, protocol):
        print('     --- Checking proxy, host:', host, ' - port:', port)
        proxies = {'https': f'{protocol}://{host}:{port}'}
        try:
            for _ in range(self.TIMES_TO_CHECK):
                r = requests.get(self.CHECKER[0],
                                 proxies=proxies, timeout=self.TIMEOUT)
                tree = fromstring(r.content)
                assert(tree.findtext('.//title') == self.CHECKER[1])
            return True
        except Exception as e:
            pass


s = Scraper()
s.load_proxies()
s.dispatch_threads()
s.save_proxies()

print(f'Got {s.get_total_live_proxies()} live proxies')

for p in s.proxy_live:
    print(p["protocol"], ' ',  p['host'], " ", p["port"])
