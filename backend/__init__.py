print ("module [backend] loaded")

from flask_cors import CORS
from flask_sqlalchemy import get_debug_queries
import os
import platform
from flask import Flask, render_template, make_response
from flask_restless import APIManager
from flask_socketio import SocketIO
from backend.server_configuration.appConfig import *
from flask_mqtt import Mqtt

import logging


# logging.basicConfig(filename = "test.log", level = logging.DEBUG)

# app = Flask(__name__)

app = Flask(__name__
            , template_folder=os.getcwd()+'/efwb-frontend/dist'
            , static_folder=os.getcwd()+'/efwb-frontend/dist/static'
            , static_url_path='/static')


cors = CORS(app, resources={r"/api/*": {"origins": "*"}}, max_age=86400)

cur_system = platform.system()
if cur_system == "Windows":
    app.config.from_object(DevelopmentConfig)
else:
    app.config.from_object(ProductionConfig)


from backend.db.database import DBManager
DBManager.init(app)

# login
from flask_login import LoginManager
login_manager = LoginManager()
login_manager.init_app(app)

# api
mqtt = Mqtt()
mqtt.init_app(app)

manager = APIManager(app, flask_sqlalchemy_db=DBManager.db)
socketio = SocketIO(app,cors_allowed_origins="*")

@app.route("/", methods=["GET"])
def page_index():
    resp = make_response(render_template("index.html"))
    return resp
@app.route("/band/", methods=["GET"])
def page_band():
    resp = make_response(render_template("index.html"))
    return resp
@app.route("/band/detail/", methods=["GET"])
def page_band_detail():
    resp = make_response(render_template("index.html"))
    return resp
@app.route("/gateway/", methods=["GET"])
def page_gateway():
    resp = make_response(render_template("index.html"))
    return resp
@app.route("/gateway/detail/", methods=["GET"])
def page_gateway_detail():
    resp = make_response(render_template("index.html"))
    return resp
@app.route("/user/", methods=["GET"])
def page_user():
    resp = make_response(render_template("index.html"))
    return resp
@app.route("/user/detail/", methods=["GET"])
def page_user_detail():
    resp = make_response(render_template("index.html"))
    return resp
@app.route("/log/", methods=["GET"])
def page_log():
    resp = make_response(render_template("index.html"))
    return resp

from backend.api.api_create import *
from backend.api.mqtt import *

server = db.session.query(Server).first()
if server.start == 0 :
    print("first")
    db.session.query(Server).filter(Server.id == 1).update(dict(start=1))
    db.session.commit()
  
else :
    print("second")
    db.session.query(Server).filter(Server.id == 1).update(dict(start=0))
    db.session.commit()
    mqtt.subscribe('/efwb/post/sync')
    mqtt.subscribe('/efwb/post/async')
    mqtt.subscribe('/efwb/post/connectcheck')
# mqtt.subscribe('/efwb/post/sync')
# mqtt.subscribe('/efwb/post/async')
# mqtt.subscribe('/efwb/post/connectcheck')

    