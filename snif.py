import os
import pyshark
import psutil

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import socket

import sys

import xml.etree.ElementTree as ET


bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
binocular_ico = os.path.abspath(os.path.join(bundle_dir, "binocular.png"))
vendors_file = os.path.abspath(os.path.join(bundle_dir, 'vendorMacs.xml'))

tree = ET.parse(vendors_file)
root = tree.getroot()



def get_ip_addresses(family):
    """ получение ip адресов и их имён для всех интерфейсов """
    for interface, snics in psutil.net_if_addrs().items():
        for snic in snics:
            if snic.family == family:
                yield (interface, snic.address)

ipv4s = list(get_ip_addresses(socket.AF_INET))
ipv6s = list(get_ip_addresses(socket.AF_INET6))
print(ipv4s)



startText = " \n 1. Отсоедини устройство, адрес которого требуется определить\n\
 2. Выбери интерфейс и нажми кнопку 'Сканирование'\n\
 3. Подсоедини устройство\n\
 P.S. Некоторые устройства придётся перезагрузить, чтобы они послали нужные пакеты"


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle("Поиск адреса устройства")        
        self.setWindowIcon(QIcon(binocular_ico))
        self.setGeometry(0, 0, 500, 200)

        toolbar = QToolBar("настройки")
        toolbar.setIconSize(QSize(16,16))
        self.addToolBar(toolbar)                     
        toolbar.setContextMenuPolicy(Qt.PreventContextMenu)    # сделать тулбар нескрываемым
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self.labelIface = QLabel()
        self.labelIface.setStatusTip("Выбор интерфейса:")
        self.labelIface.setText(" Интерфейс: ")

        self.iface = False
        self.ifaceIP = False

        self.ifaces = [name[0] for name in ipv4s]   # имена интерфейсов

        self.combo = QComboBox()

        comboboxOptions = ['-',]
        # заполнение комбобокса
        for iface in self.ifaces:
            comboboxOptions.append(iface)
        self.combo.addItems(comboboxOptions)
        self.combo.currentIndexChanged.connect(self.setIface)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        buttonStart = QAction(QIcon(binocular_ico), "Сканирование", self)
        buttonStart.setShortcut("Ctrl+R")
        buttonStart.setStatusTip("Начать прослушивание")
        buttonStart.triggered.connect(self.getAddress)

        toolbar.addWidget(self.labelIface)
        toolbar.addWidget(self.combo)
        toolbar.addWidget(spacer)
        toolbar.addAction(buttonStart)

        self.labelFound = QLabel(startText)
        self.labelFound.setAlignment(Qt.AlignLeft)
        self.labelFound.textInteractionFlags()
        self.labelFound.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setCentralWidget(self.labelFound)


    def setIface(self, ind):
        """ Получает имя локального интерфейса для прослушивания из выпадающего списка """
        self.iface = self.ifaces[ind - 1]   # назначение выбранного интерфейса
        self.ifaceIP = ipv4s[ind-1][1]      # ip адрес выбранного интерфейса
        self.labelFound.setText(f" Выбран интерфейс \n {self.iface}\n ip:{self.ifaceIP}\n Теперь нажми кнопку 'Сканирование' и подсоедини устройство")

    @staticmethod
    def getvendor(mac):
        """ Получает мак-адрес, возвращает имя производителя сетевой карты """
        try:
            mac = mac.upper()
            mac_prefix = mac[:8].upper()
            vend = 'unknown'
            for vendor in root:
                if mac_prefix == vendor.attrib['mac_prefix']:
                    vend = vendor.attrib['vendor_name']
                    break
            return vend
        except:
            return "unknown"



    def getAddress(self):
        """ Прослушивает выбранный self.iface, если найден адрес отличный от self.ifaceIP - формирует вывод в labelFound.setText """
        
        if self.iface:
            self.labelFound.setText('Выполняется сканирование...')
            print("Начинаю сканирование ", self.iface)
            capture = pyshark.LiveCapture(interface=self.iface)
            capture.sniff(timeout=2)
            # for packet in capture.sniff_continuously(packet_count=5): print(packet)
            ip = False
            mac = False
            for packet in capture:
                try:
                    test_ip = packet.ip.addr
                    test_ip = str(test_ip)
                    mac = str(packet.eth.src)
                    
                    if '0.0.0.0' not in test_ip and '169.254.' not in test_ip and test_ip != self.ifaceIP:
                        print(f'Найден адрес {test_ip}!')
                        ip = test_ip

                    if ip:
                        self.foundIp = ip
                        self.foundMac = mac
                        self.vendor = self.getvendor(mac)
                        break
                except:
                    pass
            self.labelFound.setText(f" Найдено устройство: \n=====================================================\n{self.foundIp} | {self.foundMac} | {self.vendor}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec()
