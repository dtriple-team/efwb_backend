from threading import Lock
from backend import socketio, thread_lock
from backend.db.service.query import *
from backend.api.socket import *
from backend.api.crawling import *

gateway_thread = None
airpressure_thread = None

def setGatewayLog(gid, gpid, check):
  print("[method] setGatewayLog")
  updateGatewaysConnect(gid, check)
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
    
def gatewayCheck():
  global work
  while True:
    socketio.sleep(120)
    # socketio.sleep(60)
    print("gatewayCheck start")
    work = True
    try:
      gateways = selectGatewayAll()
      for g in gateways:
        time1 = g.connect_check_time.replace(tzinfo=None)
        time2 = datetime.datetime.now(timezone('Asia/Seoul')).replace(tzinfo=None)
        if (time2-time1).seconds > 120:
          if g.connect_state==1 :
              setGatewayLog(g.id, g.pid, False)
          else:
            dev = selectGatewayLog(g.id)
            if dev is None:
              setGatewayLog(g.id, g.pid, False)

    except Exception as e:
      print(e)
    work = False

def getAirpressureTask():
  global work
  while True:
    socketio.sleep(3600)
    # socketio.sleep(60)
    print("getAltitud start")
    work = True
    dev = selectGatewayAll()
    d = datetime.datetime.now(timezone('Asia/Seoul'))
    urldate = str(d.year)+"."+str(d.month)+"."+str(d.day)+"."+str(d.hour)
    trtemp, atemp = getAirpressure(urldate)
    if trtemp != 0 :
      for g in dev:
        updateGatewaysAirpressure(g.id, searchAirpressure(trtemp, atemp, g.location))
    work = False

def gatewayCheckThread():
  global gateway_thread

  with thread_lock:
    if gateway_thread is None:
      gateway_thread = socketio.start_background_task(gatewayCheck)

def getAirpressureThread():
  global airpressure_thread

  with thread_lock:
    if airpressure_thread is None:
      airpressure_thread = socketio.start_background_task(getAirpressureTask)
