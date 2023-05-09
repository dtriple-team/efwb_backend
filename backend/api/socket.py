print ("module [socket] loaded")
from backend import socketio
from backend.api.mqtt import *
from backend.db.service.query import *

@socketio.on('connect', namespace='/receiver')
def connect():
  print("***socket connect***")
  socketio.emit("message", "connect!!", namespace='/receiver')

@socketio.on('disconnect', namespace='/receiver')
def disconnect():
    print("***socket disconnect***")

@socketio.on('message', namespace='/receiver')
def handle_message(data):
    if data == 0:
        mqttPublish('efwb/get/connectcheck', 'bandnum')
    elif data == 1:
        mqttPublish('efwb/get/connectcheck', 'bandnum')
@socketio.on('gwcheck', namespace='/receiver')
def handle_gwcheck(data):
  mqttPublish('efwb/get/'+data+"/check", 'check')

def socket_emit(topic, message):
    socketio.emit(topic, message, namespace='/receiver')

def setGatewayLog(gid, gpid, check):
  print("[method] setGatewayLog")
  updateGatewaysConnect(gid, check)
  insertGatewaysLog(gid, check)
  if check == False:
    dev =  selectBandsConnectGateway(gid)
    for b in dev:
      insertConnectBandLog(b.id, 0)
      updateConnectBands(b.id, 0)
    gateway={
      "panid": gpid,
      "bandnum": 0,
      "connectstate": False
    }
    socket_emit('gateway_connect', gateway)