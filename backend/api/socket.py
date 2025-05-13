print ("module [socket] loaded")
from backend import socketio,mqtt

from backend.db.service.query import *

@socketio.on('connect', namespace='/admin')
def connect():
  print("***socket connect***")
  socketio.emit("message", "connect!!", namespace='/admin')

@socketio.on('disconnect', namespace='/admin')
def disconnect():
    print("***socket disconnect***")

@socketio.on('message', namespace='/admin')
def handle_message(data):
    if data == 0:
        mqtt.publish('efwb/get/connectcheck', 'bandnum')
    elif data == 1:
        mqtt.publish('efwb/get/connectcheck', 'bandnum')
@socketio.on('gwcheck', namespace='/admin')
def handle_gwcheck(data):
  mqtt.publish('efwb/get/'+data+"/check", 'check')

def socket_emit(topic, message):
    socketio.emit(topic, message, namespace='/admin')

# def setGatewayLog(gid, gpid, check):
#   print("[method] setGatewayLog")
#   updateGatewaysConnect(gid, check)
#   insertGatewaysLog(gid, check)
#   if check == False:
#     dev =  selectBandsConnectGateway(gid)
#     for b in dev:
#       insertConnectBandLog(b.id, 0)
#       updateConnectBands(b.id, 0)
#     gateway={
#       "panid": gpid,
#       "bandnum": 0,
#       "connectstate": False
#     }
#     socket_emit('gateway_connect', gateway)