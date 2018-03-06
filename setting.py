import logging
import logging.handlers
# import os
# logging.basicConfig(
#     level=logging.ERROR,
#     format=
#     '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
#     datefmt='%a %d %b %Y %H:%M:%S',
#     )
formatter = logging.Formatter(
    '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%a %d %b %Y %H:%M:%S')

rotateFlieHander = logging.handlers.RotatingFileHandler(
    filename='./update.log', maxBytes=1024*1024, backupCount=1)
rotateFlieHander.setFormatter(formatter)
rotateFlieHander.setLevel(logging.ERROR)
rootLogger = logging.getLogger()
rootLogger.addHandler(rotateFlieHander)

# ROOTDIR = os.path.dirname(os.path.realpath(__file__))