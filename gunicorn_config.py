# gunicorn_config.py
bind = "0.0.0.0:10000"
workers = 1
worker_class = "eventlet"
worker_connections = 1000
timeout = 120
keepalive = 5