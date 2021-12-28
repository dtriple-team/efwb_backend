from backend import app
from backend.db.table.table_band import *

db = DBManager.db

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

def updateGatewaysConnect(gid, type):
    print("[method] updateGatewaysConnect")
    Gateways.query.filter_by(id=gid).update(dict(connect_state=type, connect_time = datetime.datetime.now(timezone('Asia/Seoul'))))
    db.session.commit()
    db.session.flush()
    db.session.close() 

def insertGatewaysLog(gid, type):
    print("[method] insertGatewaysLog")
    gatewayLog = GatewayLog()
    gatewayLog.FK_pid = gid
    gatewayLog.type = type
    db.session.add(gatewayLog) 
    db.session.commit()
    db.session.flush()
    db.session.close() 

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
    db.session.close()

def insertConnectBandLog(bid, type):
    print("[method] setBandLog")
    bandlog = BandLog()
    bandlog.FK_bid = bid
    bandlog.type = type
    db.session.add(bandlog)
    db.session.commit()
    db.session.flush()
    db.session.close()
      