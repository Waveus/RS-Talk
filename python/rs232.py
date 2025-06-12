import sys
import os
import termios
import tty
import fcntl
from enum import Enum
from PyQt5.QtCore import QThread, pyqtSignal
import select
import array
import fcntl
import time

class Confiugration():
    def __init__(self):
        self.port = None
        self.baudrate = None
        self.character_size = None
        self.parity = None
        self.flow_control = None
        self.stopbits = None
        self.terminator = None

baud_speeds: dict[int, int] = {
    150: termios.B150,
    300: termios.B300,
    600: termios.B600,
    1200: termios.B1200,
    1800: termios.B1800,
    2400: termios.B2400,
    4800: termios.B4800,
    9600: termios.B9600,
    19200: termios.B19200,
    38400: termios.B38400,
    57600: termios.B57600,
    115200: termios.B115200,
}

character_sizes: dict[int, int] = {
    8: termios.CS8,
    7: termios.CS7
}

class Parity(Enum):
    NONE = 0
    EVEN = 1
    ODD = 2

class Flow(Enum):
    XON_XOFF = 0
    DTR_DSR = 1
    RTS_CTS = 2

#DTR
TIOCM_DTR = 0x002
TIOCMGET = 0x5415
TIOCMSET = 0x5418
TIOCM_DSR = 0x100

class SerialKing:
    def __init__(self, configuration: Confiugration):
        
        self.port = configuration.port
        self.fd = None
        self.stopbits = configuration.stopbits 
        self.flow_control = configuration.flow_control
        self.baudrate = configuration.baudrate
        self.character_size = configuration.character_size
        self.terminator = configuration.terminator
        self.parity = configuration.parity

        #Opening port
        try:
            self.fd = os.open(self.port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)

        except OSError as e:
            sys.exit(1)
            pass

        self.tty_settings = termios.tcgetattr(self.fd)
        termios.tcflush(self.fd, termios.TCIFLUSH)

        #Non cannonical mode
        self.tty_settings[3] &= ~termios.ICANON
        #Turn off echo
        self.tty_settings[3] &= ~termios.ECHO

        # Wyłącz konwersje na wejściu
        self.tty_settings[0] &= ~(termios.INLCR | termios.ICRNL | termios.IGNCR)

        # Wyłącz konwersje na wyjściu
        self.tty_settings[1] &= ~termios.ONLCR

        #Speed setting up
        self.tty_settings[4] = self.baudrate #input speed
        self.tty_settings[5] = self.baudrate #output speed

        #Character size setting up
        self.tty_settings[2] &= ~termios.CS8 #clearing
        self.tty_settings[2] |= self.character_size

        #Parity setting up
        if self.parity == Parity.NONE.value:
            self.tty_settings[2] &= ~termios.PARENB
            self.tty_settings[2] &= ~termios.PARODD

        elif self.parity == Parity.EVEN.value:
            self.tty_settings[2] |= termios.PARENB
            self.tty_settings[2] &= ~termios.PARODD

        elif self.parity == Parity.ODD.value:
            self.tty_settings[2] |= termios.PARENB
            self.tty_settings[2] |= termios.PARODD
  
      
        
        #Stop bits/bit
        if self.stopbits == 2:
            self.tty_settings[2] |= termios.CSTOPB
        else:
            self.tty_settings[2] &= ~termios.CSTOPB
    
        #Turn off anything connected with Flow control
        self.tty_settings[0] &= ~termios.IXON
        self.tty_settings[0] &= ~termios.IXOFF
        self.tty_settings[2] &= ~termios.CRTSCTS

        #Set selected Flow control
        if(self.flow_control == Flow.XON_XOFF.value):
            self.tty_settings[0] |= termios.IXON | termios.IXOFF
        elif(self.flow_control == Flow.RTS_CTS.value):
            self.tty_settings[2] |= termios.CRTSCTS
        elif(self.flow_control == Flow.DTR_DSR.value):
            #TODO something
            pass
        
        termios.tcsetattr(self.fd, termios.TCSANOW, self.tty_settings)
        #self.clear_dtr()


    def set_dtr(self):
        buf = array.array('i', [0])
        fcntl.ioctl(self.fd, TIOCMGET, buf)
        status = buf[0]
        status |= TIOCM_DTR
        buf[0] = status
        fcntl.ioctl(self.fd, TIOCMSET, buf)

    def clear_dtr(self):
        buf = array.array('i', [0])
        fcntl.ioctl(self.fd, TIOCMGET, buf)
        status = buf[0]
        status &= ~TIOCM_DTR
        buf[0] = status
        fcntl.ioctl(self.fd, TIOCMSET, buf)
    
    def get_dsr(self):
        buf = array.array('i', [0])
        fcntl.ioctl(self.fd, TIOCMGET, buf)
        status = buf[0]
        dsr = bool(status & TIOCM_DSR)
        return dsr

    def write(self, data: str):
        
        if not data.endswith(self.terminator):
            data += self.terminator
            
        print('write data')
        os.write(self.fd, data.encode())


    def read(self, size=1) -> bytes:

        rlist, _, _ = select.select([self.fd], [], [], 0.1)
        if rlist:
            return os.read(self.fd, size)
        return b''

    def close(self):
        os.close(self.fd)

class SerialReaderThread(QThread):
    data_received = pyqtSignal(str)

    def __init__(self, serial_king):
        super().__init__()
        self.serial_king = serial_king
        self._running = True

    def run(self):
        buffer = ''
        while self._running:
            chunk = self.serial_king.read(1)
            if chunk:
                buffer += chunk.decode(errors='ignore')
                print(' '.join(f"0x{byte:02x}" for byte in chunk))
                if buffer.endswith(self.serial_king.terminator):
                    self.data_received.emit(buffer)
                    buffer = ''

    def stop(self):
        self._running = False
        self.wait()