from __future__ import absolute_import
from celery import Celery


app = Celery('src', backend="rpc://", broker='amqp://admin:mypass@127.0.0.1:5672', include=['src.tasks'])