# -*- coding: utf-8 -*-
print ("module [backend.api_band_create] loaded")

from backend import manager, app, DBManager
# from backend.api_common import *
from backend.db.table_band import *

db = DBManager.db
# REST API(s) available :



manager.create_api(group_table
                   , url_prefix='/api/v1'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST'])
                   
manager.create_api(user_table
                   , url_prefix='/api/v1'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST'])
manager.create_api(UsersGroups
                   , url_prefix='/api/v1'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST'])
manager.create_api(Bands
                   , url_prefix='/api/v1'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST'])
manager.create_api(UsersBands
                   , url_prefix='/api/v1'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST'])  
manager.create_api(SensorData
                   , url_prefix='/api/v1'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST'])                         
manager.create_api(Events
                   , url_prefix='/api/v1'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST'])   