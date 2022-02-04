print ("module [query] loaded")
from backend import app
from backend.db.table.table_band import *
from sqlalchemy import func, case, or_, Interval
db = DBManager.db

def getBandsEventsUser(uid, permission):
    dev = db.session.query(Events).\
      distinct(Events.datetime, Events.type).\
        filter( UsersBands.FK_uid == uid).\
          filter(UsersBands.FK_bid == Events.FK_bid).\
          group_by(Events.datetime, Events.type).\
            all()
    return dev

def getBandsEventsBands(bid):
    dev = db.session.query(Events).\
      distinct(Events.datetime, Events.type).\
        filter(Events.FK_bid==bid).\
          group_by(Events.datetime, Events.type).\
            all()
    return dev

def selectGatewayPid(pid):
    gw = db.session.query(Gateways).filter_by(pid=pid).first()
    return gw
def selectBandBid(bid):
    band = db.session.query(Bands).filter_by(bid = bid).first()
    return band

def insertGatewaysBands(pid, bid):
    gateways_bands = GatewaysBands()
    gateways_bands.FK_pid = pid
    gateways_bands.FK_bid = bid
    db.session.add(gateways_bands)
    db.session.commit()

def insertUsers():
    user = Users()
    user.uid = 2001
    user.username = "demo"
    user.password = DBManager.password_encoder_512("1234")
    user.name = "demo"
    user.permission = 1
    db.session.add(user)
    db.session.commit()

def updateBandNameAlias(bid, name, alias):
    db.session.query(Bands).filter_by(id = bid).update(dict(name=name, alias=alias))
    db.session.commit()

def updateGatewayAlias(pid, alias):
    db.session.query(Gateways).filter_by(id = pid).update(dict(alias=alias))
    db.session.commit()

def insertBandData(extAddress):
    bands = Bands()
    bands.bid = extAddress
    bands.alias = "init"
    bands.name = "init"
    bands.gender = 0
    bands.birth = "1997-09-01"
        
    db.session.add(bands)        
    db.session.commit()
    
def insertUsersGateways(uid,pid):
    users_gateways = UsersGateways()
    users_gateways.FK_pid = pid
    users_gateways.FK_uid = uid
    db.session.add(users_gateways)
    db.session.commit()

def insertUsersGroups(uid,gid):
    users_groups = UsersGroups()
    users_groups.FK_gid = gid
    users_groups.FK_uid = uid
    db.session.add(users_groups)
    db.session.commit()   

def insertUsersBands(uid, bid):
    users_bands = UsersBands()
    users_bands.FK_bid = bid
    users_bands.FK_uid = uid
    db.session.add(users_bands)
    db.session.commit()

def insertSensorData(data, ):
    data = SensorData()

def updateGatewaysIP(id, ip):
    db.session.query(Gateways).filter_by(id=id).update(dict(ip=ip))
    db.session.commit()

def insertGateway(gw):
    gateways = Gateways()
    gateways.pid = gw['panid']
    gateways.alias = "init"
    gateways.ip = gw['ip']
    gateways.location = "서울"
    db.session.add(gateways)
    db.session.commit()
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
    try:
        print("[method] selectGatewayAll")
        gateways = db.session.query(Gateways).all()
        print(gateways)
        return gateways
    except:
        print("error")
        DBManager.init(app)
        return []
    

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
      