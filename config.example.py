import datetime

RFID_READER_SERIAL = "/dev/ttyUSB0" # use /dev/serial/by-id/...
RELAY_GPIO_PIN = 4
TAG_FILE = "authorized_tags.txt"
OPEN_THRESHOLD = datetime.timedelta(seconds=5)
OPEN_TIME = 0.5