from tornado.platform.twisted import TwistedIOLoop
TwistedIOLoop().install()
from twisted.internet import reactor
from twisted.protocols import basic
from twisted.internet.serialport import SerialPort
from twisted.python import log
import tornado.web
import tornado.websocket
import tornado.ioloop
import requests
import datetime, sys
import config
import json

try:
    import RPi.GPIO as GPIO
except ImportError:
    class GPIO:
        def __getattr__(self,name):
            def method(*args):
                print 'method %s.%s called' %(self.__class__.__name__, name)
                if args:
                    print 'with args %s' % str(args)
            return method
    GPIO = GPIO()

approved_tags = []
last_open = datetime.datetime.now() - config.OPEN_THRESHOLD

with open(config.TAG_FILE, 'r') as tag_file:
    for line in tag_file.read().split('\n'):
        line = line.strip()
        if len(line) > 1:
            approved_tags += [line]

NOTIFY_CLIENTS = []

class DoorNotifyWebSocket(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True
    def open(self):
        NOTIFY_CLIENTS.append(self)
    def on_close(self):
        NOTIFY_CLIENTS.remove(self)

websocket_app = tornado.web.Application([
    (r'/notify', DoorNotifyWebSocket),
])

def notify(msg):
    msg = json.dumps(msg)
    for client in NOTIFY_CLIENTS:
        client.write_message(msg)

class RFIDSerialReader(basic.LineReceiver):
    delimiter = '\r'
    def lineReceived(self, line):
        tag = line.replace('\x02', '').replace('\x03', '').strip()
        log.msg('received tag info: %s' % tag)
        now = datetime.datetime.now()
        if tag in approved_tags and last_open + config.OPEN_THRESHOLD < datetime.datetime.now():
            log.msg('opening door for tag: %s' % tag)
            reactor.callLater(0, GPIO.output, config.RELAY_GPIO_PIN, GPIO.HIGH)
            reactor.callLater(config.OPEN_TIME, GPIO.output, config.RELAY_GPIO_PIN, GPIO.LOW)
            if config.ENDPOINT:
                reactor.callLater(0, requests.post, config.ENDPOINT, data={'CODE': tag, 'KEY': config.KEY, 'TIME': now.isoformat()})
            notify({'access_granted': True, 'time': now.isoformat()})
        elif tag not in approved_tags:
            notify({'access_granted': False, 'time': now.isoformat()})

if __name__ == "__main__":
    rfid_serial_reader = RFIDSerialReader()
    SerialPort(rfid_serial_reader, config.RFID_READER_SERIAL, reactor, baudrate='9600')

    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(config.RELAY_GPIO_PIN, GPIO.OUT)

    log.startLogging(sys.stdout)
    log.addObserver(log.FileLogObserver(open(config.LOG_FILE, 'a')).emit)

    if config.WEBSOCKET_PORT:
        websocket_app.listen(config.WEBSOCKET_PORT)

    reactor.run()
