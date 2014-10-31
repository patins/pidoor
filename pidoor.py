from twisted.internet import reactor
from twisted.protocols import basic
from twisted.internet.serialport import SerialPort
from twisted.python import log
import datetime, sys
import config

try:
    import RPi.GPIO as GPIO
except ImportError:
    # TODO dummy class
    pass

approved_tags = []
last_open = datetime.datetime.now() - config.OPEN_THRESHOLD

with open(config.TAG_FILE, 'r') as tag_file:
    for line in tag_file.read().split('\n'):
        line = line.strip()
        if len(line) > 1:
            approved_tags += [line]

class RFIDSerialReader(basic.LineReceiver):
    delimiter = '\r'
    def lineReceived(self, line):
        tag = line.strip(' \x02\x03')
        log.msg('received tag info: %s' % tag)
        if tag in approved_tags and last_open + config.OPEN_THRESHOLD < datetime.datetime.now():
            log.msg('opening door for tag: %s' % tag)
            reactor.callLater(0, GPIO.output, config.RELAY_GPIO_PIN, GPIO.HIGH)
            reactor.callLater(config.OPEN_TIME, GPIO.output, config.RELAY_GPIO_PIN, GPIO.LOW)

if __name__ == "__main__":
    rfid_serial_reader = RFIDSerialReader()
    SerialPort(rfid_serial_reader, config.RFID_READER_SERIAL, reactor, baudrate='9600')

    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(config.RELAY_GPIO_PIN, GPIO.OUT)

    log.startLogging(sys.stdout)
    log.addObserver(log.FileLogObserver(open(config.LOG_FILE, 'w')).emit)

    reactor.run()
