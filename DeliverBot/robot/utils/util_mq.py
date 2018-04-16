import redis
import time

class MQueue:
    def __init__(self):
        self._redis_client = None   #redis client object
        return

    def init_redis(self, host="localhost", port=6379, db=0, password = '', timeoutMsecs:int=60, expireMsecs:int=20):
        self._timeoutMsecs = timeoutMsecs
        self._expireMsecs = expireMsecs
        if not self._redis_client:
            self._redis_client = redis.Redis(host=host, port=port, db=db, password=password)
        return
    
    #分布式锁
    #返回锁结果，以及锁过期时间
    #获得锁最多耗时60秒(timeoutMsecs)，而加锁到释放锁总耗时10秒(expireMsecs);故锁状态下的操作有10秒时间,超过可能导致脏数据
    def redis_lock(self, lockkey:str):
        #print("争抢锁\r\n")
        timeout = self._timeoutMsecs
        while timeout >= 0:
            now = int(time.time())
            expires = now + self._expireMsecs + 1
            try:
                if self._redis_client.setnx(lockkey, expires) or (now > int(self._redis_client.get(lockkey)) and now > int(self._redis_client.getset(lockkey, expires))):
                    return True, expires
            except TypeError:
                continue
            finally:
                timeout -= 0.1
                time.sleep(0.1)
        #print("锁超时，无法获得键值\r\n")
        return False, expires

    def redis_unlock(self, lockkey:str, expires:int):
        now = int(time.time())
        if now < expires:
            #print("解锁")
            self._redis_client.delete(lockkey)
                

    def mq_with_locked(self, func, key, args=None):
        result, errmsg = None, ''
        try:
            locked, timeout = self.redis_lock(key+'lock')
            if locked:
                try:
                    result = func(key) if args is None else func(key, *args)
                except Exception as ex:
                    errmsg = ex.args
                finally:
                    self.redis_unlock(key+'lock', timeout)
            else:
                errmsg = 'locked failed!'
        finally:
            return result, errmsg


    #List操作 start
    def add_task_one(self, task_key, task_content):
        return self._redis_client.lpush(task_key, task_content)

    def add_tasks(self, task_key, *task_contents):
        """
        e.g add_tasks('task:item:queue',*[1,2,3,4,5,6])
        return: new queue count
        """
        return self._redis_client.lpush(task_key, *task_contents)

    def add_task_onef(self, task_key, task_content):
        """
        Prepend one or multiple values to a list
        """
        return self._redis_client.rpush(task_key, task_content)

    def add_tasksf(self, task_key, *task_contents):
        """
        Prepend one or multiple values to a list
        e.g add_tasks('task:item:queue',*[6,5,4,3,2,1])
        return: new queue count
        """
        return self._redis_client.rpush(task_key, *task_contents)

    def get_task_one(self, task_key):
        return self._redis_client.rpop(task_key)

    def get_tasks(self, task_key, count):
        """
        redis not support,
        """
        result = [self._redis_client.rpop(task_key)]
        while len(result) < count:
            result.append(self._redis_client.rpop(task_key))
        return result

    def view_count(self, task_key):
        return self._redis_client.llen(task_key)

    def view_tasks(self, task_key, start, end):
        return self._redis_client.lrange(task_key,start,end)
    #List操作 end

    #hash操作 start
    def add_hash_one(self, dic_name, hash_key, hash_value):
        """
            success: 1
            exist: 0
        """
        return self._redis_client.hset(dic_name, hash_key, hash_value)

    def add_hashs(self, dic_name, mapping):
        return self._redis_client.hmset(dic_name, mapping)

    def get_hash_one(self, dic_name, hash_key):
        return self._redis_client.hget(dic_name, hash_key)

    def get_hashs(self, dic_name, hash_key_list):
        return self._redis_client.hmget(dic_name, hash_key_list)

    def get_hash_all(self, dic_name):
        return self._redis_client.hgetall(dic_name)

    def is_exists_hash(self, dic_name, hash_key):
        return self._redis_client.hexists(dic_name, hash_key)

    def del_hash_one(self, dic_name, hash_key):
        return self._redis_client.hdel(dic_name, hash_key)
    #hash操作 end

    def del_key(self, dic_name):
        return self._redis_client.delete(dic_name)