from contextlib import nullcontext
from os import device_encoding
from backend import app
from backend.db.table.table_band import *
from sqlalchemy import func, Interval
from sqlalchemy.sql.expression import text
db = DBManager.db

def selectSameGroupOfUser(uid):
    group = db.session.query(Groups).\
        filter(Groups.id == UsersGroups.FK_gid).\
            filter(UsersGroups.FK_uid==uid).\
                first()
    return group

def datetimeBetween(data):
  if len(data) == 1 :
    return data[0]
  else :
    return data[len(data)-1]

def selectBandsEventsUser(uid, permission):
    dev = None
    if permission == 0:
        dev = selectBandsEvents()
        return dev
    elif permission == 1:
        dev = selectBandsEventsUserStaff(uid)
        return dev
    elif permission == 2:
        dev = selectBandsEventsUserMmanager(uid)
        return dev
    elif permission == 3:
        dev = selectBandsEventsUserMmanager(uid)
        return dev
    return dev

def selectBandsEventsUserStaff(uid):
    group = selectSameGroupOfUser(uid)
    dev = db.session.query(Events).\
        distinct(Events.datetime, Events.type).\
             filter(UsersGroups.FK_gid == group.id).\
                filter(UsersBands.FK_uid == UsersGroups.FK_uid).\
                    filter(Events.FK_bid == UsersBands.FK_bid).\
                        group_by(Events.datetime, Events.type).\
                            all()
    
    return dev

def selectBandsEventsUserMmanager(uid):
    dev = db.session.query(Events).\
        distinct(Events.datetime, Events.type).\
            filter(UsersBands.FK_uid == uid).\
                filter(UsersBands.FK_bid == Events.FK_bid).\
                    group_by(Events.datetime, Events.type).\
                        all()
    return dev

def selectBandsEventsUserUser(uid):
    dev = db.session.query(Events).\
        distinct(Events.datetime, Events.type).\
            filter(UsersBands.FK_uid == uid).\
                filter(UsersBands.FK_bid == Events.FK_bid).\
                    group_by(Events.datetime, Events.type).\
                        all()
    return dev

def selectBandsEventsBands(bid):
    dev = db.session.query(Events).\
      distinct(Events.datetime, Events.type).\
        filter(Events.FK_bid==bid).\
          group_by(Events.datetime, Events.type).\
            all()
    return dev

def selectBandsEvents():
    dev = db.session.query(Events).\
      distinct(Events.datetime, Events.type).\
        group_by(Events.datetime, Events.type).\
          all()
    return dev

def selectBandsEventsUserDate(uid, permission, date):
    print("selectBandsEventsUserDate")
    if permission == 0:
        dev = selectBandsEventsDate(date)
        return dev
    elif permission == 1:
        dev = selectBandsEventsUserStaff(uid, date)
        return dev
    elif permission == 2:
        dev = selectBandsEventsUserMmanager(uid, date)
        return dev
    elif permission == 3:
        dev = selectBandsEventsUserMmanager(uid, date)
        return dev

def selectBandsEventsUserStaff(uid, date):
    group = selectSameGroupOfUser(uid)
    dev = db.session.query(Events).\
        distinct(Events.datetime, Events.type).\
             filter(UsersGroups.FK_gid == group.id).\
                filter(UsersBands.FK_uid == UsersGroups.FK_uid).\
                    filter(UsersBands.FK_bid == Events.FK_bid).\
                        filter(func.date(Events.datetime).\
                            between(date[0], datetimeBetween(date))).\
                                group_by(Events.datetime, Events.type).all()
    
    return dev

def selectBandsEventsUserMmanager(uid, date):
    dev = db.session.query(Events).\
      distinct(Events.datetime, Events.type).\
        filter( UsersBands.FK_uid == uid).\
          filter(UsersBands.FK_bid == Events.FK_bid).\
            filter(func.date(Events.datetime).\
                between(date[0], datetimeBetween(date))).\
                    group_by(Events.datetime, Events.type).all()
    return dev

def selectBandsEventsUserUser(uid):
    dev = db.session.query(Events).\
        distinct(Events.datetime, Events.type).\
            filter(UsersBands.FK_uid == uid).\
                filter(UsersBands.FK_bid == Events.FK_bid).\
                    group_by(Events.datetime, Events.type).\
                        all()
    return dev

def selectBandsEventsBandDate(bid, date):
    dev = db.session.query(Events).\
        distinct(Events.datetime, Events.type).\
        filter(Events.FK_bid==bid).\
          filter(func.date(Events.datetime).\
            between(date[0], datetimeBetween(date))).\
              group_by(Events.datetime, Events.type).all()
    return dev

def selectBandsEventsDate(date):
    dev = db.session.query(Events).\
        distinct(Events.datetime, Events.type).\
          filter(func.date(Events.datetime).\
            between(date[0], datetimeBetween(date))).\
              group_by(Events.datetime, Events.type).all()
    return dev

def selectFallDetectDate(date, format):
    dev = db.session.query(func.date_format(Events.datetime, format).label('day'),
    func.sum(Events.value).label('fall')).\
        filter(Events.type==0).\
            filter(func.date_format(Events.datetime, '%Y-%m-%d').\
                between(func.date_add(func.now(), text('interval -1 '+date)), func.now())).\
                    group_by(func.date_format(Events.datetime, "%Y-%m-%d")).all()
    return dev

def selectFallDetectDateStaff(uid, date, format ):
    group = selectSameGroupOfUser(uid)
    dev = db.session.query(func.date_format(Events.datetime, format).label('day'),
    func.sum(Events.value).label('fall')).\
        filter(UsersGroups.FK_gid == group.id).\
            filter(UsersBands.FK_uid == UsersGroups.FK_uid).\
                filter(Events.FK_bid == UsersBands.FK_bid).\
                    filter(Events.type==0).\
                        filter(func.date_format(Events.datetime, '%Y-%m-%d').\
                            between(func.date_add(func.now(), text('interval -1 '+date)), func.now())).\
                    group_by(func.date_format(Events.datetime, "%Y-%m-%d")).all()
    return dev

def selectFallDetectDateManager(uid, date, format):
    dev = db.session.query(func.date_format(Events.datetime, format).label('day'),
    func.sum(Events.value).label('fall')).\
        filter(UsersBands.FK_uid == uid).\
            filter(UsersBands.FK_bid == Events.FK_bid).\
              filter(Events.type==0).\
                filter(func.date_format(Events.datetime, '%Y-%m-%d').\
                  between(func.date_add(func.now(), text('interval -1'+ date)), func.now())).\
                  group_by(func.date_format(Events.datetime, "%Y-%m-%d")).all()
    return dev

def selectFallDetectDateUser(uid, date, format):
    dev = db.session.query(func.date_format(Events.datetime, format).label('day'),
    func.sum(Events.value).label('fall')).\
        filter(UsersBands.FK_uid == uid).\
            filter(UsersBands.FK_bid == Events.FK_bid).\
              filter(Events.type==0).\
                filter(func.date_format(Events.datetime, '%Y-%m-%d').\
                  between(func.date_add(func.now(), text('interval -1'+ date)), func.now())).\
                  group_by(func.date_format(Events.datetime, "%Y-%m-%d")).all()
    return dev

