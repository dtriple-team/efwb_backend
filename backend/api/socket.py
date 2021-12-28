print ("module [socket] loaded")
from backend import socketio

@socketio.on('connect', namespace='/receiver')
def connect():
  print("***socket connect***")

@socketio.on('disconnect', namespace='/receiver')
def disconnect():
    print("***socket disconnect***")

@socketio.on('message', namespace='/receiver')
def handle_message(data):
    print('received message: ' + data)

def socket_emit(topic, message):
    socketio.emit(topic, message, namespace='/receiver')