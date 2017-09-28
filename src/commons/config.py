import os
import getpass

ES_HOST = os.environ.get('ES_HOST', '34.230.32.193')
ES_PORT = os.environ.get('ES_PORT', 9200)
ES_URL = 'http://' + ES_HOST + ":" + str(ES_PORT)
ES_LOG_INDEX = os.environ.get('ES_LOG_INDEX', "_".join(["logging", getpass.getuser()]))
ENV = os.environ.get('ENV', "DEV")
APP = os.environ.get('APP', getpass.getuser())
