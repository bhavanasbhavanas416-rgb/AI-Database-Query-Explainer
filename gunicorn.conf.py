import os

bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
workers = int(os.getenv('WEB_CONCURRENCY', '3'))
worker_class = 'sync'
timeout = 120
keepalive = 5
loglevel = 'info'
accesslog = '-'
errorlog = '-'
