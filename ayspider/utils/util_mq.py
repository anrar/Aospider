import redis

class MQueue:
    def __init__(self):
        self._redis_client = None   #redis client object
        return

    def init_redis(self, host="localhost", port=6379, db=0,password = ''):
        if not self._redis_client:
            self._redis_client = redis.Redis(host=host, port=port, db=db, password=password)
        return
    
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