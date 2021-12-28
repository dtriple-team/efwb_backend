from threading import Lock
from backend import socketio

gateway_thread = None
mqtt_thread = None
airpressure_thread = None
thread_lock = Lock()
example_thread = None
gw_thread = None
work = False