import logging

from cmreslogging.handlers import CMRESHandler
from config import *


def enrich_es_handler():
    return CMRESHandler(hosts=[{'host_ip': ES_HOST, 'port': ES_PORT}], auth_type=CMRESHandler.AuthType.NO_AUTH, es_index_name=ES_LOG_INDEX, es_additional_fields={'App': APP, 'Environment': ENV})


handler = enrich_es_handler()
log = logging.getLogger("CrawlerES")
log.setLevel(logging.INFO)
log.addHandler(handler)
