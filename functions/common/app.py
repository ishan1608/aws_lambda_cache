import os
import time

from apig_wsgi import make_lambda_handler
from flask import Flask, request, current_app, g as app_ctx

MODULE_PATH = os.environ['MODULE_PATH']

# Flask app
app = Flask(__name__)


@app.before_request
def log_request_info():
    app.logger.info(f'Method: {request.method} URL: {request.url}')
    app.logger.info('Headers: %s', request.headers)
    # Store the start time for the request
    app_ctx.start_time = time.perf_counter()


_lambda_handler = make_lambda_handler(app)


# Configure this as your entry point in AWS Lambda
def lambda_handler(event, context):
    # noinspection PyCallingNonCallable
    return _lambda_handler(event, context)


@app.after_request
def after_request(response):
    # Get total time in milliseconds
    total_time = time.perf_counter() - app_ctx.start_time
    time_in_ms = int(total_time * 1000)
    # Log the time taken for the endpoint
    current_app.logger.info('request_time_taken: %s ms %s %s %s %s', time_in_ms, request.method, request.path,
                            dict(request.args), request.url)

    return response


@app.route(f'{MODULE_PATH}/cache/get', methods=['GET'])
def cache_get():
    from pymemcache.client import base

    # Get the ElastiCache endpoint from the environment variable
    memcache_endpoint = os.environ['CACHE_ENDPOINT']
    # memcache_endpoint = 'localhost'

    # Connect to the ElastiCache cluster
    client = base.Client((memcache_endpoint, 11211))

    # Set a value in the cache
    value = client.get('test_key', b'fallback').decode('utf-8')

    return value, {'Content-Type': 'text/plain'}


@app.route(f'{MODULE_PATH}/cache/set', methods=['GET'])
def cache_set():
    from pymemcache.client import base

    # Get the ElastiCache endpoint from the environment variable
    memcache_endpoint = os.environ['CACHE_ENDPOINT']
    # memcache_endpoint = 'localhost'

    # Connect to the ElastiCache cluster
    client = base.Client((memcache_endpoint, 11211))

    # Set a value in the cache
    client.set('test_key', request.args.get('name', 'ALC'))

    return 'Saved to cache', {'Content-Type': 'text/plain'}
