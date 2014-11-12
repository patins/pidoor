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

APPROVED_USERS = []
last_open = datetime.datetime.now() - config.OPEN_THRESHOLD

with open(config.TAG_FILE, 'r') as tag_file:
    for line in tag_file.read().split('\n'):
        line = line.strip()
        if len(line) > 1:
            line = line.split(',')
            APPROVED_USERS += [(line[0], ''.join(line[1:]))]

def authorize(tag):
    for user in APPROVED_USERS:
        if user[0] == tag:
            return user[1]
    return None

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
        user = authorize(tag)
        if user and last_open + config.OPEN_THRESHOLD < datetime.datetime.now():
            log.msg('opening door for: %s' % user)
            reactor.callLater(0, GPIO.output, config.RELAY_GPIO_PIN, GPIO.HIGH)
            reactor.callLater(config.OPEN_TIME, GPIO.output, config.RELAY_GPIO_PIN, GPIO.LOW)
            if config.ENDPOINT:
                reactor.callLater(0, requests.post, config.ENDPOINT, data={'CODE': tag, 'user': user, 'KEY': config.KEY, 'TIME': now.isoformat()}, verify=False)
            notify({'access_granted': True, 'user': user, 'time': now.isoformat()})
        elif not user and last_open + config.OPEN_THRESHOLD < datetime.datetime.now():
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
