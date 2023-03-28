#!/usr/bin/python
# параметры компиляции для pyinstaller
# pyinstaller nscanner.spec
from csv import writer          # для сохранения в csv
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import nscan
import os
import snif
import sys
import webbrowser

bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
network_ico = os.path.abspath(os.path.join(bundle_dir, "network-ethernet.png"))
start_ico = os.path.abspath(os.path.join(bundle_dir, "magnifier-zoom.png"))
save_ico = os.path.abspath(os.path.join(bundle_dir, "floppy-disk.png"))
binocular_ico = os.path.abspath(os.path.join(bundle_dir, "binocular.png"))

#################### default settings ############################################
hostname = nscan.socket.gethostname() 
local_ip = nscan.socket.gethostbyname(hostname).split('.')
local_ip[3] = '1'
local_ip = '.'.join([i for i in local_ip])
nscan.prefix = local_ip 
nscan.packets = "1"
nscan.waittime = "1"


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.liveHosts = []                             # собирает ip адреса
        self.liveMacs = []                              # собирает (ip, mac,vendor)
        self.setWindowTitle("binoculars v.0.2")        
        self.setWindowIcon(QIcon(network_ico))
        self.setGeometry(0, 0, 700, 400)

#### TOOLBAR ######################################################################################
        toolbar = QToolBar("настройки")
        toolbar.setIconSize(QSize(16,16))
        self.addToolBar(toolbar)                     
        toolbar.setContextMenuPolicy(Qt.PreventContextMenu)    # сделать тулбар нескрываемым
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self.labelNet = QLabel()
        self.labelNet.setStatusTip("Задать сеть для сканирования")
        self.labelNet.setText(" Сеть: ")
        self.inputNet = QLineEdit()
        self.inputNet.setFixedWidth(100)
        self.inputNet.setText(nscan.prefix)
        
        self.labelPackets = QLabel()
        self.labelPackets.setStatusTip("Количество пакетов для хоста (чем больше, тем точнее пройдёт сканирование)")
        self.labelPackets.setText(" Пакеты:")
        self.inputPackets = QLineEdit()
        self.inputPackets.setFixedWidth(30)
        self.inputPackets.setText(nscan.packets)

        self.labelWait = QLabel()
        self.labelWait.setText(" Ожидание: ")
        self.labelWait.setStatusTip("Время ожидания ответа от хоста (чем больше, тем точнее пройдёт сканирование)")
        self.inputWait = QLineEdit()
        self.inputWait.setFixedWidth(30)
        self.inputWait.setText(nscan.waittime)

        self.labelCheckboxMac = QLabel()
        self.labelCheckboxMac.setStatusTip("Показать/скрыть колонки MAC и VENDOR")
        self.labelCheckboxMac.setText(" Определять MAC:")
        self.checkboxMac = QCheckBox()
        self.checkboxMac.stateChanged.connect(self.showMac)
        self.macHide = True                              # переменная, для определения скрыты колонки мак и вендор или нет


        buttonBinocular = QAction(QIcon(binocular_ico), "Сниффер", self)
        buttonBinocular.setStatusTip("Найти адрес устройства")
        buttonBinocular.setShortcut("Ctrl+B")
        buttonBinocular.triggered.connect(self.binocular)

        buttonStart = QAction(QIcon(start_ico), "Начать", self)
        buttonStart.setStatusTip("Начать сканирование")
        buttonStart.setShortcut("Ctrl+R")
        buttonStart.triggered.connect(self.start)


        buttonSave = QAction(QIcon(save_ico), "Сохранить", self)
        buttonSave.setShortcut("Ctrl+S")
        buttonSave.setStatusTip("Сохранить результаты в файл")
        buttonSave.triggered.connect(self.saveFile)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        toolbar.addWidget(self.labelNet)
        toolbar.addWidget(self.inputNet)
        toolbar.addWidget(self.labelPackets)
        toolbar.addWidget(self.inputPackets)
        toolbar.addWidget(self.labelWait)
        toolbar.addWidget(self.inputWait)
        toolbar.addWidget(self.labelCheckboxMac)
        toolbar.addWidget(self.checkboxMac)
        toolbar.addWidget(spacer)
        toolbar.addSeparator()

        toolbar.addAction(buttonBinocular)
        toolbar.addAction(buttonSave)
        toolbar.addAction(buttonStart)


#### STATUSBAR ##################################################################
        self.setStatusBar(QStatusBar(self))                    # статусбар

        # вертикальный контейнер
        self.mainLayout = QVBoxLayout()
    
        self.mainWidget = QWidget()
        self.mainWidget.setLayout(self.mainLayout)
        self.statusBar().showMessage(f'Сеть для сканирования: {nscan.prefix}/24  Время ожидания хоста: {nscan.waittime} ms  Количество пакетов: {nscan.packets}', 1000000)


#### TABLE ##########################################################################
        self.tableWidget = QTableWidget()
  
        #Row count
        self.rowCount = 0
        self.tableWidget.setRowCount(0)
        self.tableWidget.resizeRowsToContents() 
        self.tableWidget.resizeColumnsToContents() 
        #Column count
        self.tableWidget.setColumnCount(3)
        self.tableWidget.horizontalHeader().sectionClicked.connect(self.headClick)   # действия при нажатии на заголовок
  
        self.tableWidget.setHorizontalHeaderItem(0, QTableWidgetItem('IP'))
        self.tableWidget.setHorizontalHeaderItem(1, QTableWidgetItem('MAC'))
        self.tableWidget.setHorizontalHeaderItem(2, QTableWidgetItem('VENDOR'))

        self.tableWidget.hideColumn(1)                    # по умолчанию колонка мак адресов скрыта
        self.tableWidget.hideColumn(2)                    # по умолчанию колока Vendor скрыта

        #Table will fit the screen horizontally
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.mainLayout.addWidget(self.tableWidget)

        self.tableWidget.cellActivated.connect(self.ipClick)             # при нажатии Enter выбранный ip открывается в браузере

        self.setCentralWidget(self.mainWidget)


    def binocular(self):
        """ Открывает окно снифера """

        isInstalled = False
        if nscan.os_type == 'win':
            paths = ['C:\\Program Files\\Wireshark\\', 'C:\\Program Files (x86)\\Wireshark\\', 'C:\\Program Files\\Wireshark\\']
            for path in paths:
                for root, dirs, files in os.walk(path):
                    if 'tshark.exe' in files:
                        isInstalled = True
        if nscan.os_type == 'linux':
            paths = ['/usr/bin/', '/bin/', '/usr/local/sbin']
            for path in paths:
                for root, dirs, files in os.walk(path):
                    if 'tshark' in files:
                        isInstalled = True


        if isInstalled:
            self.binocularWindow = snif.MainWindow()
            self.binocularWindow.show()

        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Ошибка!")
            msg.setInformativeText('''
Похоже, что не установлен Wireshark\n\
Не найден файл tshark.exe по адресам\n\
C:\\Program Files\\Wireshark\\tshark.exe\n\
C:\\Program Files (x86)\\Wireshark\\tshark.exe\n\
C:\\Program Files\\Wireshark\\tshark.exe''')
            msg.setWindowTitle("Error")
            msg.exec_()


    def headClick(self, index):
        """ при клике на заголовок таблицы """
        if index in (1, 2):
            self.fillMac()


    def start(self):
        """ Действия при нажатии кнопки начала сканирования """
        self.liveHosts = []                    # обнуляем списки прошлых сканирований
        self.liveMacs = []
        self.rowCount = 0 
        self.tableWidget.setRowCount(0)

        nscan.prefix = self.inputNet.text()           # получаем сеть для сканирования
        nscan.waittime = self.inputWait.text()        # получаем время ожидания хоста
        nscan.packets = self.inputPackets.text()      # получаем количество пакетов, которое должно быть послано
        
        i = 0
        for host in nscan.ping_all():
            self.liveHosts.append(host)
            self.rowCount += 1
            self.tableWidget.setRowCount(self.rowCount)
            ip = QTableWidgetItem(host)
            ip.setForeground(QColor(0, 153, 0))
            self.tableWidget.setItem(i, 0, ip)
            i += 1
        if self.macHide == False:
            self.fillMac()

    def fillMac(self):
        """ получаем мак и вендор для всех живых хостов """
        i = 0
        for host in self.liveHosts:
            mac = nscan.getMac(host)
            vendor = nscan.getvendor(mac)
            self.tableWidget.setItem(i, 1, QTableWidgetItem(mac))
            self.tableWidget.setItem(i, 2, QTableWidgetItem(vendor))
            self.liveMacs.append((host, mac, vendor))
            i += 1


    def ipClick(self, row, column):
        """ Открыть браузер для адреса в ячейке (работает, только если нажать Enter)"""
        if column == 0:
            try:
                ip = self.tableWidget.item(row, column).text()
                webbrowser.open(f"http://{ip}")
            except:
                self.statusBar().showMessage(f'Невозможно открыть адрес', 1000000)

    def showMac(self, state):
        if state == 2:
            self.tableWidget.showColumn(1)
            self.tableWidget.showColumn(2)
            self.macHide = False
        else:
            self.tableWidget.hideColumn(1)
            self.tableWidget.hideColumn(2)
            self.macHide = True

    def saveFile(self):
        if len(self.liveHosts) > 0:
            file_name = "output.csv"
            default_dir ="."
            default_filename = os.path.join(default_dir, file_name)
            name, _ = QFileDialog.getSaveFileName(self, "Save csv file", default_filename, "CSV Files (*.csv)")
            if name:
                if len(self.liveMacs) > 0 and self.macHide == False:
                    """ Записать адреса, маки и вендоров """
                    with open(name, "w") as file:
                        csv_writer = writer(file)
                        csv_writer.writerow(["ip", "mac", "vendor"])
                        for host in self.liveMacs:
                            csv_writer.writerow([host[0], host[1], host[2]])
                else:
                    """  Записать только живые адреса """
                    with open(name, "w") as file:
                        csv_writer = writer(file)
                        csv_writer.writerow(["ip"])
                        for host in self.liveHosts:
                            csv_writer.writerow([host])
        else:
            self.statusBar().showMessage(f'Сперва нужно запустить сканирование', 1000000)


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
