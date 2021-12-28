from backend import app, socketio

def socket_emit(topic, message):
    socketio.emit(topic, message, namespace='/receiver')