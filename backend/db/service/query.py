print ("module [query] loaded")
from backend import app
from backend.db.table.table_band import *
from sqlalchemy import func, case, or_, Interval
db = DBManager.db

def selectGatewayPid(pid):
    dev = db.session.query(Gateways).filter_by(pid=pid).first()
    return dev
def insertSensorData(data, ):
    data = SensorData()

def insertEvent(id, type, value):
    events = Events()
    events.FK_bid = id
    events.type = type
    events.value = value
    events.datetime = datetime.datetime.now()
    db.session.add(events)
    db.session.commit()
    db.session.flush()  
    
def selectGatewayLog(gid):
    print("[method] selectGatewayLog")
    gatewaylog = GatewayLog.query.filter_by(FK_pid=gid).first()
    return gatewaylog

def selectGatewayAll():
    print("[method] selectGatewayAll")
    gateways = db.session.query(Gateways).all()
    return gateways

def updateGatewaysAirpressure(gid, airpressure):
    db.session.query(Gateways).filter_by(id = gid).update((dict(airpressure=airpressure)))
    db.session.commit()
def updateGatewaysConnectCheck(gid):
    db.session.query(Gateways).filter_by(id=gid).\
        update(dict(connect_check_time=datetime.datetime.now(timezone('Asia/Seoul'))))
    db.session.commit()
    db.session.flush()
def updateGatewaysConnect(gid, type):
    print("[method] updateGatewaysConnect")
    getTime = datetime.datetime.now(timezone('Asia/Seoul'))
    if type:
        Gateways.query.filter_by(id=gid).\
            update(dict(connect_state=1, connect_time = getTime, connect_check_time=getTime))
    else : 
         Gateways.query.filter_by(id=gid).\
             update(dict(connect_state=0, disconnect_time = getTime))
    db.session.commit()
    db.session.flush()


def insertGatewaysLog(gid, type):
    print("[method] insertGatewaysLog")
    gatewayLog = GatewayLog()
    gatewayLog.FK_pid = gid
    gatewayLog.type = type
    db.session.add(gatewayLog) 
    db.session.commit()
    db.session.flush()
    # db.session.close() 

def selectBandsConnectGateway(gid):
    print("[method] selectBandsConnectGateway")
    dev = db.session.query(Bands).\
        filter(Bands.connect_state == 1).\
            filter(Bands.id == GatewaysBands.FK_bid).\
                filter(GatewaysBands.FK_pid == gid).all()
    return dev

def updateConnectBands(bid , type):
    print("[method] updateConnectBands")
    Bands.query.filter_by(id = bid).update(dict(
          disconnect_time=datetime.datetime.now(timezone('Asia/Seoul'))
          , connect_state = type))
    db.session.commit()
    db.session.flush()

def insertConnectBandLog(bid, type):
    print("[method] setBandLog")
    bandlog = BandLog()
    bandlog.FK_bid = bid
    bandlog.type = type
    db.session.add(bandlog)
    db.session.commit()
    db.session.flush()
      