from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QSettings
import sys
import serial
import serial.tools.list_ports
import  time
import pyqtgraph as pg
import pyqtgraph.exporters
import math
import numpy as np
import random
import collections
serial_port =  serial.Serial()

class Serial_RX(QtCore.QThread):
    Serial_signal = pyqtSignal()
    serial_display = ''
    mode = 'ASCII'
    timer = time.clock()
    def __init__(self):
        QtCore.QThread.__init__(self)
    def __del__(self):
        self.wait()
    def run(self):
        while True:
            if serial_port.is_open:
                try:
                    if serial_port.inWaiting()>0:
                        delta_time = (time.clock() - self.timer)
                        self.timer = time.clock()
                        #print(delta_time)
                        bytesToRead = serial_port.inWaiting()
                        data = serial_port.read(bytesToRead)
                        self.serial_display = ''

                        if(self.mode == 'ASCII'):
                            self.serial_display += data.decode("utf-8")

                        elif(self.mode == 'HEX'):
                            if delta_time> 0.025:
                                self.serial_display += '\r\n'
                            for b in data:
                                self.serial_display +=  ' '+format(b, '02x')+' '

                        self.Serial_signal.emit()
                except:
                    print('read error')
class Serial_TX(QtCore.QThread):
    data_to_send = ''
    def __init__(self,data_to_send):
        QtCore.QThread.__init__(self)
        self.data_to_send = data_to_send
    def __del__(self):
        self.wait()
    def run(self):
        try:
            serial_port.write(self.data_to_send.encode())
        except:
            print('send error')
class main_widget(QWidget):
    x_plt_arr =  np.array([])
    y_plt_arr = np.array([])
    def __init__(self, parent,settings):
        self.settings = settings
        super().__init__(parent)
        self.setupUI()
    def get_port_list(self):
        port_list = []
        for i in serial.tools.list_ports.comports(include_links=False):
            port_list.append(i.device)
        return port_list
    def update_port_list(self):
        print('update_port_list')
        self.Port_select.clear()
        self.Port_select.addItems(self.get_port_list())
        self.Port_select.update()
    def serial_connect(self):

        serial_port.port = str(self.Port_select.currentText())

        serial_port.baudrate = int(self.Buad_select.currentText())
        print(serial_port)
        try:
            serial_port.open()
        except:
            print('Serial error')
            self.serial_error_dialog()
            return
        self.connection_update()
        print('Connected')
        self.serial_log_clear()
        self.settings.setValue('last_connect_port', serial_port.port)
        self.settings.setValue('last_connect_baud', str(serial_port.baudrate))
    def serial_disconnect(self):
        serial_port.close()
        self.connection_update()
        print('Disconnected')
    def serial_log_update(self):
        self.Serial_log.insertPlainText(self.Serial_RX_Thread.serial_display)
        self.Serial_log.verticalScrollBar().setValue(self.Serial_log.verticalScrollBar().maximum())
    def serial_log_clear(self):
        self.Serial_log.setPlainText('')
    def connection_update(self):
        if serial_port.is_open:#connected
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)

            self.Port_select.setEnabled(False)
            self.port_refresh_button.setEnabled(False)
            self.Buad_select.setEnabled(False)
            self.send_button.setEnabled(True)
            self.ASCII_mode.setEnabled(False)
            self.HEX_mode.setEnabled(False)
        else:
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            self.Port_select.setEnabled(True)
            self.port_refresh_button.setEnabled(True)
            self.Buad_select.setEnabled(True)
            self.send_button.setEnabled(False)
            self.ASCII_mode.setEnabled(True)
            self.HEX_mode.setEnabled(True)
    def serial_send(self):
        data_to_send = self.text_for_send.text()
        if self.CR.isChecked():
            data_to_send += '\r'
        if self.NL.isChecked():
            data_to_send += '\n'
        self.Serial_TX_Thread = Serial_TX(data_to_send)
        self.Serial_TX_Thread.start()
        print('send : ' + data_to_send)

        self.text_for_send.setText('')
        pass
    def serial_error_dialog(self):
        serial_error_msg = QMessageBox()
        serial_error_msg.setIcon(QMessageBox.Warning)
        serial_error_msg.setText("Error openning serial port "+serial_port.port)
        #serial_error_msg.setInformativeText("This is additional information")
        serial_error_msg.setWindowTitle("Warning message")

        serial_error_msg.setStandardButtons(QMessageBox.Ok )
        serial_error_msg.exec_()
    def serial_setting_groupBox(self):
        serial_setting = QGroupBox('Serial port setting')
        Hlayout = QHBoxLayout(self)
        l1 = QLabel()
        l1.setText('Port')
        l2 = QLabel()
        l2.setText('Baud rate')
        self.port_refresh_button = QPushButton('Refresh', self)
        self.port_refresh_button.clicked.connect(self.update_port_list)

        self.connect_button = QPushButton('Connect', self)
        self.connect_button.clicked.connect(self.serial_connect)
        self.disconnect_button = QPushButton('Disconnect', self)
        # self.disconnect_button.setEnabled(False)
        self.disconnect_button.clicked.connect(self.serial_disconnect)

        self.Port_select = QComboBox()
        port_list = self.get_port_list()
        self.Port_select.addItems(port_list)

        last_connect_port = self.settings.value('last_connect_port', type=str)
        if last_connect_port in port_list:
            self.Port_select.setCurrentIndex(port_list.index(last_connect_port))

        self.Buad_select = QComboBox()
        baud_list = ['300', '600', '1200', '2400', '4800', '9600', '14400', '19200', '28800', '38400', '57600', '115200']
        self.Buad_select.addItems(baud_list)
        last_connect_baud = self.settings.value('last_connect_baud', type=str)
        if last_connect_baud in baud_list:
            self.Buad_select.setCurrentIndex(baud_list.index(last_connect_baud))


        H_Spacer1 = QSpacerItem(150, 10, QSizePolicy.Expanding)
        Hlayout.addWidget(l1)
        Hlayout.addWidget(self.Port_select)
        Hlayout.addWidget(self.port_refresh_button)
        Hlayout.addWidget(l2)
        Hlayout.addWidget(self.Buad_select)
        Hlayout.addWidget(self.connect_button)
        Hlayout.addWidget(self.disconnect_button)
        Hlayout.addItem(H_Spacer1)
        # Vlayout.addLayout(Hlayout_0)
        serial_setting.setLayout(Hlayout)
        return serial_setting
    def update_display_mode(self,btn):
        print('update display_mode to '+btn.text())
        self.Serial_RX_Thread.mode = btn.text()

    def log_display_setting_groupBox(self):
        log_display_setting = QGroupBox('Display setting')
   
        Hlayout = QHBoxLayout(self)
        l1 = QLabel()
        l1.setText('Display mode')
        self.ASCII_mode = QRadioButton("ASCII")
        self.ASCII_mode.setChecked(True)
        self.ASCII_mode.clicked.connect(lambda:self.update_display_mode(self.ASCII_mode))
        self.HEX_mode = QRadioButton("HEX")
        self.HEX_mode.clicked.connect(lambda:self.update_display_mode(self.HEX_mode))
        clear_log_button = QPushButton('Clear', self)
        clear_log_button.clicked.connect(self.serial_log_clear)
        H_Spacer = QSpacerItem(150, 10, QSizePolicy.Expanding)
        Hlayout.addWidget(l1)
        Hlayout.addWidget(self.ASCII_mode)
        Hlayout.addWidget(self.HEX_mode)
        Hlayout.addWidget(clear_log_button)
        Hlayout.addItem(H_Spacer)
        log_display_setting.setLayout(Hlayout)

        return log_display_setting
    def setupUI(self):
        self.Serial_RX_Thread = Serial_RX()
        self.Serial_RX_Thread.start()
        self.Serial_RX_Thread.Serial_signal.connect(self.serial_log_update)
        Vlayout = QVBoxLayout(self)
        ################################

        Vlayout.addWidget(self.serial_setting_groupBox())

        ################################
        Vlayout.addWidget(self.log_display_setting_groupBox())



        self.Serial_log = QPlainTextEdit()

        self.Serial_log.setReadOnly(True)

        Vlayout.addWidget(self.Serial_log)

        ################################
        Hlayout_1 = QHBoxLayout(self)
        self.text_for_send = QLineEdit()
        self.send_button = QPushButton('Send', self)
        self.send_button.clicked.connect(self.serial_send)
        Hlayout_1.addWidget(self.text_for_send)
        Hlayout_1.addWidget(self.send_button)
        Vlayout.addLayout(Hlayout_1)

        ################################
        Hlayout_2 = QHBoxLayout(self)
        l3 = QLabel()
        l3.setText('Line ending')
        self.CR = QCheckBox("<CR>")
        self.NL = QCheckBox("<NL>")
        H_Spacer2 = QSpacerItem(150, 10, QSizePolicy.Expanding)


        Hlayout_2.addWidget(l3)
        Hlayout_2.addWidget(self.CR)
        Hlayout_2.addWidget(self.NL)
        Hlayout_2.addItem(H_Spacer2)
        Vlayout.addLayout(Hlayout_2)
        ################################
        self.connection_update()
        self.setLayout(Vlayout)
class main_window(QMainWindow):
    def __init__(self,settings ):
        self.settings = settings


        super(QMainWindow, self).__init__()
        #QMainWindow.__init__(self)
        self.initUI()
    def initUI(self):
        self.setGeometry(300, 300, 500, 600)
        self.setWindowTitle("Serial Monitor")
        self.setWindowIcon(QtGui.QIcon('py_logo.png'))
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('File')
        impMenu = QMenu('Import', self)
        imp_txt_Act = QAction('Import text file', self)
        imp_csv_Act = QAction('Import CSV file', self)
        imp_byte_Act = QAction('Import Protocol file', self)
        impMenu.addAction(imp_txt_Act)
        impMenu.addAction(imp_csv_Act)
        impMenu.addAction(imp_byte_Act)

        expMenu = QMenu('Export', self)
        exp_txt_Act = QAction('Export text file', self)
        exp_csv_Act = QAction('Export CSV file', self)
        exp_byte_Act = QAction('Export Protocol file', self)
        expMenu.addAction(exp_txt_Act)
        expMenu.addAction(exp_csv_Act)
        expMenu.addAction(exp_byte_Act)

        fileMenu.addMenu(impMenu)
        fileMenu.addMenu(expMenu)

        editMenu = mainMenu.addMenu('Edit')
        viewMenu = mainMenu.addMenu('View')
        toolsMenu = mainMenu.addMenu('Tools')
        helpMenu = mainMenu.addMenu('Help')
        self.main_widget = main_widget(self,self.settings)
        self.setCentralWidget( self.main_widget)

class plotter(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.setWindowTitle("Scope")
        self.setWindowIcon(QtGui.QIcon('py_logo.png'))
        self.setupUI()

    def setupUI(self):
        V_main_layout = QVBoxLayout(self)
        self.GLW = pg.GraphicsLayoutWidget()
        V_main_layout.addWidget(self.GLW)
        self.setLayout(V_main_layout)
        self.plt = self.GLW.addPlot()
        self.plt.setLabel('bottom', 'Time', 's')
        self.plt.setLabel('left', 'Magnitude')
        self.x = np.arange(0.0,10.0,0.01)
        self.y = np.sin(self.x*2*np.pi/10.0)
        self.plt.plot(self.x, self.y)
        self.plt.showGrid(x=True, y=True)
    def update(self):
        self.plt.plot(self.x, self.y,clear=True)





def main():
    app = QApplication(sys.argv)
    settings = QSettings('Meng\'s Lab', 'Serial Monitor')
    w = main_window(settings)
    w.show()
    #s = plotter()
    #s.show()
    #width = w.frameGeometry().width()
    #height = w.frameGeometry().height()
    #print(width,height)
    exit(app.exec_())



if __name__ == '__main__':
    main()