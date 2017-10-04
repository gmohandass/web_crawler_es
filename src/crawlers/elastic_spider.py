from elasticsearch  import Elasticsearch
from commons.config import ES_URL
from datetime import datetime as dt
import subprocess 
import scrapy 
import json 
import uuid
import base64

class ElasticSpider(scrapy.Spider):
	'''
	All that's needed is to define an "index_name" variable in your 
	spider class (which defines the name of the index in ElasticSearch), 
	and then call "self.exists_in_db" or "self.add_to_db".
	'''

	def __init__(self, *args, **kwargs):
		''' Check if index exists, and create if not '''
		self._ES_OBJ = Elasticsearch([ES_URL])
		indices = self._query_db('_cat/indices')
		if self.index_name not in indices:
			self.log('Creating index: %s' % self.index_name)
			resp = self._query_db(self.index_name, 'XPUT')
			assert('acknowledged' in resp and resp['acknowledged']), \
				'Failed creating index: %s' % resp
		super(ElasticSpider, self).__init__(*args, **kwargs)


	def exists_in_db(self, uid, key='uid'):
		''' Checks if the given uid exists in the database. 
			Assumes uid is stored in a key called 'uid',
			though that can be changed '''
		data = {"query": {"match_phrase": {key: uid}}}
		resp = self._query_db('%s/_search' % self.index_name, data=data)
		return 'hits' in resp and 'total' in resp['hits'] and int(resp['hits']['total']) 


	def add_to_db(self, data):
		''' Add a document to the database - "data" should be a dictionary '''
		data['timestamp'] = dt.now()
		data['data'] = base64.b64encode(data['data'].encode())
		# resp = self._query_db('%s/doc/' % self.index_name, 'XPOST', data=data)
		# return 'created' in resp and resp['created']
		self._ES_OBJ.index( index=self.index_name, 
							doc_type="html",
							id=str(uuid.uuid1()),
							body=data,
							pipeline="attachment")
		

	def _query_db(self, path, method="XGET", flags="", data="", verbose=True):
		''' Helper method to send commands to the ElasticSearch database 

		Parameters
		----------
		path   : string following final "/" after the database url, e.g.
				 "_cat/indices"  
		method : type of curl request - ["XGET", "XPUT", "XDELETE", "XPOST", ...]
		flags  : any extra flags to send to curl
		data   : any data sent via -d flag 
		verbose: whether to log sent cmd / received response

		Returns
		-------
		resp   : response from the curl command, parsed as json if possible
		'''
		cmd  =  """curl -s -%s %s/%s """ % (method, ES_URL, path) + \
				"""%s -H "Content-Type: application/json" """ % flags

		if data: # Doubling json.dumps escapes double quotes
			cmd += """-d %s """ % json.dumps(json.dumps(data))
		
		if verbose: self.log('Sending command: %s' % cmd)
		resp = subprocess.check_output(cmd).decode('utf-8')
		if verbose: self.log('Received response: %s' % str(resp))
		try:    resp = json.loads(resp)
		except: pass 
		return resp
