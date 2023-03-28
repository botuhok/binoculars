# SuperFastPython.com
# scan a range of port numbers on a host concurrently
import argparse
import socket
from concurrent.futures import ThreadPoolExecutor
from sys import platform
import os
import sys
import xml.etree.ElementTree as ET

# Абсолютные пути до файлов 
bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
vendors_file = os.path.abspath(os.path.join(bundle_dir, 'vendorMacs.xml'))


if platform == 'linux' or platform == 'linux2' or platform == 'cygwin' or platform == 'darwin':
    os_type = 'linux'


if platform == 'win32' or platform == 'windows':
    os_type = 'win'




tree = ET.parse(vendors_file)
root = tree.getroot()

home = {'68:D9:3C:A1:34:CF': 'iPhone 4',
        'B8:76:3F:A6:24:FB': 'Lenovo_wlan',
        '9C:5A:81:01:3D:A4': 'Redmi 9',
        '02:81:C6:14:B2:1E': 'OrangePi',
        '30:14:4A:4B:6D:E3': 'lenovo-net',
        '40:F0:2F:3A:18:C5': 'Asus(Hryumka)',
        'd8:97:ba:3d:64:64': 'Lenovo_eth0',
        '04:5E:A4:57:34:74': 'Netis N4_lan',
        '04:5E:A4:57:34:7B': 'Netis N4_wan',
        '04:5E:A4:57:34:75': 'Netis N4_wifi',
        '48:8F:5A:6B:6C:8B': 'Microtic hAP',
        '48:8F:5A:6B:6C:8A': 'Microtic hAP(port1)',
        '00:25:D3:18:4C:BC': 'ASUS Bodhi',
        '48:9D:24:09:95:1D': 'BlackBerry Q10',
        'E8:9F:6D:94:2F:0F': 'NodeMCU temp mon.',
        }



prefix = "192.168.1.1"
packets = "1"
waittime = "1"



def getvendor(mac):
    """ Получает мак-адрес, возвращает имя производителя сетевой карты """
    # get vendor from xml table
    try:
        mac = mac.upper()
        if mac in home:
            return home[mac]
        mac_prefix = mac[:8].upper()
        vend = 'unknown'
        for vendor in root:
            if mac_prefix == vendor.attrib['mac_prefix']:
                vend = vendor.attrib['vendor_name']
                break
        return vend
    except:
        return "unknown"


def ping(ip):
    """ Пингует адрес, если ответ есть вернёт True """
    if os_type == 'linux':
        ret = os.system(f'ping -c {packets} -W {waittime} {ip} > /dev/null 2>/dev/null')

    if os_type == 'win':
        ret = os.system(f'ping -n {packets} -w {waittime} {ip} > NUL')

    if ret == 0: return True
    return False


def getMac(ip):
    if platform == 'linux' or platform == 'linux2' or platform == 'cygwin' or platform == 'darwin':
        import arpreq
        mac = arpreq.arpreq(ip)

    if platform == 'win32' or platform == 'windows':
        import getmac
        mac = getmac.get_mac_address(ip=ip, network_request=True)

    if mac: return mac
    return "unknown"


def ping_all():
    """ Пингует диапазон он 1 до 256 через multithreading"""
    # create the thread pool
    list_ip = [prefix[:-1] + str(i) for i in range(1, 256)]
    with ThreadPoolExecutor(len(list_ip)) as executor:
        # dispatch all tasks
        results = executor.map(ping, list_ip)
        # report results in order
        for ip, is_live in zip(list_ip, results):
            if is_live:
                #mac = getMac(ip)
                yield ip
                #yield (ip, mac, getvendor(mac))


