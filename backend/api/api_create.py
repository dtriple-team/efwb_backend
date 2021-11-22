# -*- coding: utf-8 -*-
print ("module [backend.api_band_create] loaded")

from backend import manager, app, DBManager
# from backend.api_common import *
from backend.db.table_band import *
from backend.api.api_band import *
db = DBManager.db
# REST API(s) available :

manager.create_api(Groups
                   , url_prefix='/api/v1'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST']
                   , preprocessors={
                        'GET_SINGLE': [check_token],
                        'GET_MANY': [check_token],
                        'POST': [check_token],
                        'PATCH': [check_token]
                    })
manager.create_api(AccessHistory
                   , url_prefix='/api/v1'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST']
                   , preprocessors={
                        'GET_SINGLE': [check_token],
                        'GET_MANY': [check_token],
                        'POST': [check_token],
                        'PATCH': [check_token]
                    })                   
manager.create_api(Users
                   , url_prefix='/api/v1'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST']
                   , preprocessors={
                        'GET_SINGLE': [check_token],
                        'GET_MANY': [check_token],
                        'POST': [check_token],
                        'PATCH': [check_token]
                    })
manager.create_api(UsersGroups
                   , url_prefix='/api/v1'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST']
                   , preprocessors={
                        'GET_SINGLE': [check_token],
                        'GET_MANY': [check_token],
                        'POST': [check_token],
                        'PATCH': [check_token]
                    })
manager.create_api(Bands
                   , url_prefix='/api/v1'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST']
                   , preprocessors={
                        'GET_SINGLE': [check_token],
                        'GET_MANY': [check_token],
                        'POST': [check_token],
                        'PATCH': [check_token]
                    })
manager.create_api(UsersGateways
                   , url_prefix='/api/v1'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST']
                   , preprocessors={
                        'GET_SINGLE': [check_token],
                        'GET_MANY': [check_token],
                        'POST': [check_token],
                        'PATCH': [check_token]
                    })
manager.create_api(GatewaysBands
                   , url_prefix='/api/v1'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST']
                   , preprocessors={
                        'GET_SINGLE': [check_token],
                        'GET_MANY': [check_token],
                        'POST': [check_token],
                        'PATCH': [check_token]
                    })                  
manager.create_api(SensorData
                   , url_prefix='/api/v1'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST']
                   , preprocessors={
                        'GET_SINGLE': [check_token],
                        'GET_MANY': [check_token],
                        'POST': [check_token],
                        'PATCH': [check_token]
                    })                         
manager.create_api(Events
                   , url_prefix='/api/v1'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST']
                   , preprocessors={
                        'GET_SINGLE': [check_token],
                        'GET_MANY': [check_token],
                        'POST': [check_token],
                        'PATCH': [check_token]
                    })   
manager.create_api(GatewayLog
                   , url_prefix='/api/v1'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST']
                   , preprocessors={
                        'GET_SINGLE': [check_token],
                        'GET_MANY': [check_token],
                        'POST': [check_token],
                        'PATCH': [check_token]
                    }) 
manager.create_api(BandLog
                   , url_prefix='/api/v1'
                   , methods=['GET', 'DELETE', 'PATCH', 'POST']
                   , preprocessors={
                        'GET_SINGLE': [check_token],
                        'GET_MANY': [check_token],
                        'POST': [check_token],
                        'PATCH': [check_token]
                    }) 