from celery import Celery

app = Celery('tasks', backend="rpc://", broker='amqp://127.0.0.1')


@app.task
def publish_to_es(es, url, website_name):
    es.publish_doc(url, website_name)


@app.task
def publish_to_es_bulk(es, url, website_name):
    es.bulk_publish_docs(url, website_name)
