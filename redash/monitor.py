import json
from redash import redis_connection, models, __version__, settings


def get_status():
    status = {}
    info = redis_connection.info()
    status['redis_used_memory'] = info['used_memory']
    status['redis_used_memory_human'] = info['used_memory_human']
    status['version'] = __version__
    status['queries_count'] = models.db.session.query(models.Query).count()
    if settings.FEATURE_SHOW_QUERY_RESULTS_COUNT:
        status['query_results_count'] = models.db.session.query(models.QueryResult).count()
        status['unused_query_results_count'] = models.QueryResult.unused().count()
    status['dashboards_count'] = models.Dashboard.query.count()
    status['widgets_count'] = models.Widget.query.count()

    status['workers'] = []

    status['manager'] = redis_connection.hgetall('redash:status')
    status['data_sources'] = json.loads(redis_connection.get('data_sources:health') or '{}')

    queues = {}
    for ds in models.DataSource.query:
        for queue in (ds.queue_name, ds.scheduled_queue_name):
            queues.setdefault(queue, set())
            queues[queue].add(ds.name)

    status['manager']['queues'] = {}
    for queue, sources in queues.iteritems():
        status['manager']['queues'][queue] = {
            'data_sources': ', '.join(sources),
            'size': redis_connection.llen(queue)
        }
    
    status['manager']['queues']['celery'] = {
        'size': redis_connection.llen('celery'),
        'data_sources': ''
    }

    status['database_metrics'] = []
    # have to include the fake FROM in the SQL to prevent an IndexError
    queries = [
        ['Query Results Size', "pg_size_pretty(pg_total_relation_size('query_results')) as size from (select 1) as a"],
        ['Redash DB Size', "pg_size_pretty(pg_database_size('postgres')) as size from (select 1) as a"]
    ]
    for query_name, query in queries:
        result = models.db.session.query(query).first()
        status['database_metrics'].append([query_name, result[0]])

    return status
