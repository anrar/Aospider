# _*_ coding: utf-8 _*_

"""
producer
监控队列消息数量,低于指定数量则添加新消息(现在数据从mysql中读)
"""
from .producer import Producer
from .prod_task import ProducerTask
