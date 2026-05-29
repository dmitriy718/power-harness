import logging

logger = logging.getLogger("nova_agent")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

def get_logger(name: str = "nova_agent"):
    return logger.getChild(name)
