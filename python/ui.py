from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QTextEdit, QPushButton, QLabel
)

from PyQt5.QtGui import QFont

import sys
from rs232 import SerialKing
from rs232 import SerialReaderThread
from rs232 import Flow
import time

class MainWindow(QMainWindow):
    def __init__(self, _serialKing : SerialKing):
        super().__init__()
        self.setWindowTitle("RS232 KING")
        self.serialKing = _serialKing

        self.setFixedSize(800, 600)

        central_widget = QWidget()
        layout = QVBoxLayout()

        label_layout = QHBoxLayout()
        edit_text_layout = QHBoxLayout()
        button_layout = QHBoxLayout()
        ping_layout = QHBoxLayout()

        #Selecting font
        font = QFont()
        font.setPointSize(14)

        #Recived data
        self.recived_label = QLabel()
        self.recived_label.setText('Recived data')
        self.recived_label.setFont(font)
        self.read_text = QTextEdit()
        self.read_text.setReadOnly(True)

        #Data to send
        self.to_send_label = QLabel()
        self.to_send_label.setText('Data to send')
        self.to_send_label.setFont(font)
        self.write_text = QTextEdit()

        # Przycisk Send
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_data)

        # Przycisk Clear
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear)

        # Przycisk Ping
        self.ping_button = QPushButton("Ping")
        self.ping_button.clicked.connect(self.ping)

        self.ping_label = QLabel()
        self.ping_label.setText('Ping[ms]:')

        label_layout.addWidget(self.recived_label)
        label_layout.addWidget(self.to_send_label)

        edit_text_layout.addWidget(self.read_text)
        edit_text_layout.addWidget(self.write_text)

        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.send_button)

        ping_layout.addWidget(self.ping_button)
        ping_layout.addWidget(self.ping_label)

        # Dodanie do głównego layoutu
        layout.addLayout(label_layout)
        layout.addLayout(edit_text_layout)
        layout.addLayout(button_layout)
        layout.addLayout(ping_layout)


        # Przypisanie layoutu
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


        self.reader_thread = SerialReaderThread(self.serialKing)
        self.reader_thread.data_received.connect(self.update_read_text)
        self.reader_thread.start()

    def send_data(self):
        data = self.write_text.toPlainText()
        if data:
            data: str = data + self.serialKing.terminator
            data_bytes = data.encode()
            if self.serialKing.flow_control != Flow.DTR_DSR.value:
                self.serialKing.write(data=data_bytes)
                self.write_text.clear()
            else:
                self.reader_thread.sending_data = True
                timeout = 1
                start_time = time.time()
                while not self.serialKing.get_dsr():
                    if time.time() - start_time > timeout:
                        self.serialKing.set_dtr()
                        print("DSR not received within timeout.")
                        self.reader_thread.sending_data = False
                        return
                    time.sleep(0.001)

                self.reader_thread.sending_data = False
                self.serialKing.write(data_bytes)
                self.write_text.clear()

    def clear(self):
        self.read_text.clear()
        pass

    def ping(self):
        self.reader_thread.pong_received = False  # Resetuj flagę
        start_time = time.time()

        self.serialKing.write(data=b'\x00')

        timeout = 3
        while time.time() - start_time < timeout:
            QApplication.processEvents()
            if self.reader_thread.pong_received:
                elapsed = (time.time() - start_time) * 1000
                self.ping_label.setText(f"Ping[ms]: {elapsed:.2f}")
                return

        self.ping_label.setText("Ping timeout (>3s)")



    def update_read_text(self, data):
        print(data)
        self.read_text.insertPlainText(data)

    def closeEvent(self, event):
        self.reader_thread.stop()
        event.accept()