import datetime

RFID_READER_SERIAL = "/dev/ttyUSB0" # use /dev/serial/by-id/...
RELAY_GPIO_PIN = 7
TAG_FILE = "authorized_tags.csv"
OPEN_THRESHOLD = datetime.timedelta(seconds=5)
OPEN_TIME = 5
LOG_FILE = "door.log"
