import time
import logging
from robot import utils
from robot.robot import ManagerBot

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s][%(thread)d][%(levelname)s]\t%(message)s",datefmt='%m-%d %H:%M')
    fh = logging.FileHandler(filename ="log/"+str(int(time.time()))+".log",mode ="a",encoding = "utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter('[%(asctime)s][%(thread)d][%(levelname)s]\t%(message)s'))
    logging.getLogger('').addHandler(fh)


bot_infos = [
            {'api_key':'A61C08B7F3928DE07E57E7C5BA3F1ADC',
                'steamid':'76561198413403307',
                'shared_secret':'28pPiF4/W516muNyuRG9/KNncHY=',
                'identity_secret':'CKKMU4SWv4/GB2Uhqa2Q9MbXZ+I=',
                'username':'aycjdw',
                'password':'AoYoucj01',
                'trade_url':'https://steamcommunity.com/tradeoffer/new/?partner=453137579&token=vWUKqinU',
                'is_buyer': False}
             ,
             {'api_key':'EED222BD0D467C878FA94BFE3A2F1702',
                'steamid':'76561198414064980',
                'shared_secret':'OqFInWnV0xe0blB1G5ywg0x2EiE=',
                'identity_secret':'A0UQuxgCC9AQhbZuXOQKcb+KCiU=',
                'username':'niubility360',
                'password':'qwe789456qwe',
                'trade_url':'https://steamcommunity.com/tradeoffer/new/?partner=453799252&token=kbSUsH5N',
                'is_buyer': True}
                ]

mq = utils.MQueue()
mq.init_redis()

mb = ManagerBot(bot_infos, mq)
mb.start()
logging.info('main thread start')
