from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import pyqtSignal
import sys
import serial
import serial.tools.list_ports
serial_port =  serial.Serial()

class Serial_RX(QtCore.QThread):
    Serial_signal = pyqtSignal()
    serial_display = ''
    def __init__(self,):
        QtCore.QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        while True:
            if serial_port.is_open:
                try:
                    if serial_port.inWaiting()>0:

                            bytesToRead = serial_port.inWaiting()
                            data = serial_port.read(bytesToRead)
                            self.serial_display = self.serial_display + data.decode("utf-8")
                            #print(data.decode("utf-8") )
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




class main_window(QWidget):
    def __init__(self):
        super().__init__()
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

    def serial_disconnect(self):
        serial_port.close()
        self.connection_update()
        print('Disconnected')


    def serial_log_update(self):
        #print('serial_log_update')
        self.Serial_log.setText(self.Serial_RX_Thread.serial_display)
        self.Serial_log.verticalScrollBar().setValue(self.Serial_log.verticalScrollBar().maximum())
    def connection_update(self):
        if serial_port.is_open:
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)

            self.Port_select.setEnabled(False)
            self.port_refresh_button.setEnabled(False)
            self.Buad_select.setEnabled(False)
            self.send_button.setEnabled(True)
        else:
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            self.Port_select.setEnabled(True)
            self.port_refresh_button.setEnabled(True)
            self.Buad_select.setEnabled(True)
            self.send_button.setEnabled(False)
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

    def setupUI(self):
        self.setGeometry(300,300, 500,700)
        self.setWindowTitle("Serial Monitor")
        self.setWindowIcon(QtGui.QIcon('py_logo.png'))

        Vlayout = QVBoxLayout(self)
        ################################
        Hlayout_0 = QHBoxLayout(self)
        l1 = QLabel()
        l1.setText('Port')
        l2 = QLabel()
        l2.setText('Baud rate')
        self.port_refresh_button = QPushButton('Refresh', self)
        self.port_refresh_button.clicked.connect(self.update_port_list)

        self.connect_button = QPushButton('Connect', self)
        self.connect_button.clicked.connect(self.serial_connect)
        self.disconnect_button = QPushButton('Disconnect', self)
        #self.disconnect_button.setEnabled(False)
        self.disconnect_button.clicked.connect(self.serial_disconnect)

        self.Port_select = QComboBox()
        self.Port_select.addItems(self.get_port_list())

        self.Buad_select = QComboBox()

        self.Buad_select.addItems(['300', '600', '1200', '2400', '4800', '9600', '14400', '19200', '28800', '38400', '57600', '115200'])
        self.Buad_select.setCurrentIndex(5)
        H_Spacer1 = QSpacerItem(150, 10, QSizePolicy.Expanding)
        Hlayout_0.addWidget(l1)
        Hlayout_0.addWidget(self.Port_select)
        Hlayout_0.addWidget(self.port_refresh_button)
        Hlayout_0.addWidget(l2)
        Hlayout_0.addWidget(self.Buad_select)
        Hlayout_0.addWidget(self.connect_button)
        Hlayout_0.addWidget(self.disconnect_button)
        Hlayout_0.addItem(H_Spacer1)
        Vlayout.addLayout(Hlayout_0)
        ################################

        self.Serial_log = QTextEdit()
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
        self.Serial_RX_Thread = Serial_RX()
        self.Serial_RX_Thread.start()
        self.Serial_RX_Thread.Serial_signal.connect(self.serial_log_update)
        self.connection_update()

        self.show()

def main():

    app = QApplication(sys.argv)
    w = main_window()
    width = w.frameGeometry().width()
    height = w.frameGeometry().height()

    exit(app.exec_())



if __name__ == '__main__':
    main()