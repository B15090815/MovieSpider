import logging
logging.basicConfig(
    level=logging.ERROR,
    format=
    '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%a %d %b %Y %H:%M:%S', 
    filemode="a")

rootLogger = logging.getLogger("root")
# ch = logging.StreamHandler()
# formatter = logging.Formatter(
#     '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
#     datefmt='%a %d %b %Y %H:%M:%S',
# )
# ch.setFormatter(formatter)
# rootLogger.addHandler(ch)
rotateFlieHander = logging.handlers.RotatingFileHandler(
    filename='update.log', maxBytes=1024*1024, backupCount=1)
rootLogger.addHandler(rotateFlieHander)
# logging.root.addHandler(rotateFlieHander)
