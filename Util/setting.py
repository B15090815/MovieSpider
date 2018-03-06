import logging
import logging.handlers
logging.basicConfig(
    level=logging.ERROR,
    format=
    '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%a %d %b %Y %H:%M:%S',
    filemode="a",
    filename='./update.log')

rootLogger = logging.getLogger("root")
rotateFlieHander = logging.handlers.RotatingFileHandler(
    filename='update.log', maxBytes=1024*1024, backupCount=1)
rootLogger.addHandler(rotateFlieHander)
# logging.root.addHandler(rotateFlieHander)
