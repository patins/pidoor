from twisted.internet import reactor
from twisted.protocols import basic
from twisted.internet.serialport import SerialPort
from twisted.python import log
import datetime
import config

try:
    import RPi.GPIO as GPIO
except ImportError:
    # TODO dummy class
    pass

approved_tags = []
last_open = datetime.datetime.now()

with open(config.TAG_FILE, 'r') as tag_file:
    for line in tag_file.read().split('\r\n'):
        line = line.split()
        if len(line) > 1:
            approved_tags += [line]

class RFIDSerialReader(basic.LineReceiver):
    delimiter = '\r'
    def lineReceived(self, line):
        log.msg('received scan info: %s' % line)
        if tag in approved_tags and last_open + config.OPEN_THRESHOLD < datetime.datetime.now():
            reactor.callLater(0, GPIO.output, config.RELAY_GPIO_PIN, GPIO.HIGH)
            reactor.callLater(config.OPEN_TIME, GPIO.output, config.RELAY_GPIO_PIN, GPIO.LOW)

if __name__ == "__main__":
    rfid_serial_reader = RFIDSerialReader()
    SerialPort(rfid_serial_reader, config.RFID_READER_SERIAL, reactor, baudrate='9600')

    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(config.RELAY_GPIO_PIN, GPIO.OUT)

    reactor.run()