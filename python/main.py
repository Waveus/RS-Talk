import sys
import os
import termios
import tty
import glob
import rs232
from rs232 import SerialKing
from PyQt5.QtWidgets import QApplication
from ui import MainWindow
import codecs

baud_speeds: dict[str, int] = {
    '150': termios.B150,
    '300': termios.B300,
    '600': termios.B600,
    '1200': termios.B1200,
    '1800': termios.B1800,
    '2400': termios.B2400,
    '4800': termios.B4800,
    '9600': termios.B9600,
    '19200': termios.B19200,
    '38400': termios.B38400,
    '57600': termios.B57600,
    '115200': termios.B115200,
}

parity_types : dict[str, int] = {
    'NONE' : 0,
    'EVEN' : 1,
    'ODD' : 2,
}
    
flows : dict[str, int] = {
    'XON_XOFF' : 0,
    'DTR_DSR' : 1,
    'RTS_CTS' : 2,
    'NONE': 3,
}
    
character_sizes: dict[str, int] = {
    '8': termios.CS8,
    '7': termios.CS7
}

stop_bits : dict[str, int]= {
    '1': 1,
    '2': 2,
}

def find_ports() -> list[str]:
    
    device_patterns: list[str] = ['/dev/ttyS*', '/dev/ttyUSB*', '/dev/ttyV*']
    found_ports: list[str] = []

    for pattern in device_patterns:
        found_ports.append(glob.glob(pattern))

    found_ports = [port for sublist in found_ports for port in sublist]

    return found_ports if not [] else None

def choose_terminator() -> str:
    
    option = ''
    term = ''
    is_ok = False

    while(not is_ok):
        
        option = input('1. Standard CR\n2. Standard LF\n3. Standard CR+LF\n4.Own 1 or 2 char\nEnter option: ')

        match option:
            case '1':
                term = '\r'
                is_ok = True
            case '2':
                term = '\n'
                is_ok = True
            case '3':
                term = '\r\n'
                is_ok = True
            case '4':
                raw_input = input('Enter custom terminator): ')
                try:
                    term = codecs.decode(raw_input, 'unicode_escape')
                    if 1 <= len(term) <= 2:
                        is_ok = True
                    else:
                        print("Custom terminator must be 1 or 2 characters long.")
                except Exception as e:
                    print("Invalid escape sequence:", e)
            case _:
                print("Invalid option.")
        
    return term

class Confiugration():
    def __init__(self):
        self.port = None
        self.baudrate = None
        self.character_size = None
        self.parity = None
        self.flow_control = None
        self.stopbits = None
        self.terminator = None

def configure_serial():

    configuration = Confiugration()
    avaliable_ports = find_ports()
    is_ok = False

    #Selecting port
    while(not is_ok):
        print("Avaliable ports:")
        for port in avaliable_ports:
            print(f"-{port}")
        selected = input("Select port (enter full path): ")
        if(selected in avaliable_ports):
            is_ok = True
            configuration.port = selected

    is_ok = False

    #Selecting baudrate
    while(not is_ok):
        

        print("Avaliable baudrates:")
        for baudrate in baud_speeds.keys():
            print(f"-{baudrate}")
        
        selected = input("Enter baudrate: ")

        if(selected in baud_speeds.keys()):
            is_ok = True
            configuration.baudrate = baud_speeds[selected]
    
    is_ok = False

    #Selecting character_size

    while(not is_ok):
        
        print("Avaliable character sizes:")
        for character_size in character_sizes.keys():
            print(f"-{character_size}")

        selected = input("Enter character size: ")

        if(selected in character_sizes.keys()):
            is_ok = True
            configuration.character_size = character_sizes[selected]
    
    is_ok = False

    #Selecting parity
    while(not is_ok):
    
        print("Avaliable parity types:")
        for parity_type in parity_types.keys():
            print(f"-{parity_type}")
        
        selected = input("Enter parity type: ")

        if(selected in parity_types.keys()):
            is_ok = True
            configuration.parity = parity_types[selected]
    
    is_ok = False
    
    #Selecting flow control
    
    while(not is_ok):
        
        print("Avaliable flow control:")
        for flow in flows.keys():
            print(f"-{flow}")

        selected = input("Enter flow type: ")

        if(selected in flows.keys()):
            is_ok = True
            configuration.flow_control = flows[selected]
    
    is_ok = False

    #Selecting stop bits
    
    while(not is_ok):

        print("Avaliable stop bits:")
        for stop_bit in stop_bits.keys():
            print(f"-{stop_bit}")

        selected = input("Enter how many stop bits: ")

        if(selected in stop_bits.keys()):
            is_ok = True
            configuration.stopbits = stop_bits[selected]

    #Selecting terminator

    configuration.terminator = choose_terminator()

    return configuration


def run_UI(king):
    app = QApplication(sys.argv)

    window = MainWindow(_serialKing=king)
    window.show()

    app.exec()

def run():

    confiugration : Confiugration = configure_serial()
    
    print('Selected configuration:')
    print(f'Port: {confiugration.port}')
    print(f'Baudrate: {confiugration.baudrate}')
    print(f'Character size: {confiugration.character_size}')
    print(f'Parity: {confiugration.parity}')
    print(f'Flow control: {confiugration.flow_control}')
    print(f'Stop bits: {confiugration.stopbits}')
    print("Hex:", ' '.join(f"0x{ord(c):02x}" for c in confiugration.terminator))

    king = SerialKing(confiugration)
    run_UI(king)
 


if __name__ == '__main__':
    run()
