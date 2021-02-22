import logging

logger = logging.getLogger()
handler = logging.FileHandler('tmp/log.txt')
formatter = logging.Formatter(
				'%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)