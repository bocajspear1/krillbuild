import configparser
import logging

logger = logging.getLogger('krillbuild')

class Config():

    def __init__(self, config_path="./krill.ini"):
        parser = configparser.ConfigParser()
        data = parser.read(config_path)

        logger.info("Loading configuration")

        print(parser.sections())

        self._main = dict(parser['main'])
        print(self._main)

    @property
    def main_config(self):
        return self._main
