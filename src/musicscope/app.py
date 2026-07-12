from .config import Config
from .logger import get_logger
class MusicScopeApp:
    def __init__(self):
        self.cfg=Config()
        self.log=get_logger()
    def run(self):
        self.log.info('%s %s',self.cfg.app_name,self.cfg.version)
        print('\n=================')
        print(' MusicScope')
        print('=================')
        print('Bootstrap OK')
