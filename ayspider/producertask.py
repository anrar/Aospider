import logging
from ayspider import utils
from ayspider import prod

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s\t%(levelname)s\t%(message)s")

logging.debug("count:%s prevcount:%s", 1, 2)
mq = utils.MQueue()
mq.init_redis(host='9', password ='fsdsfd')
sqlconn = utils.Mysql(host='', port=20633, user='', password='', db='')

produ = prod.ProducerTask(mq, sqlconn, '1','5', 10)                #1,4,5,6,7,9
produ.start()
print('exit')

