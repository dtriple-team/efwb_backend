print ("module [backend] loaded")

from flask_cors import CORS
from flask_sqlalchemy import get_debug_queries
import os
import platform
import threading
from flask import Flask, render_template, make_response
from flask_restless import APIManager
from flask_socketio import SocketIO
from backend.server_configuration.appConfig import *
from flask_mqtt import Mqtt


# app = Flask(__name__)

app = Flask(__name__
            , template_folder=os.getcwd()+'/efwb-frontend/dist'
            , static_folder=os.getcwd()+'/efwb-frontend/dist/static'
            , static_url_path='/static')


cors = CORS(app, resources={r"/api/*": {"origins": "*"}}, max_age=86400)
app.config['MQTT_BROKER_URL'] = "t-vsm.com"
app.config['MQTT_BROKER_PORT'] = 18831



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
mqtt = Mqtt(app)
manager = APIManager(app, flask_sqlalchemy_db=DBManager.db)
socketio = SocketIO(app, cors_allowed_origins="*", engineio_logger=False)


from backend.api.api_create import *

def gatewayCheckThread():

    gatewayth = threading.Thread(target=gatewayCheck)
    airpressureth = threading.Thread(target=getAirpressure)
    gatewayth.start()
    airpressureth.start()
    gatewayth.join() 
    airpressureth.join()
     
# gatewayCheckThread()

@app.route("/", methods=["GET"])
def page_index():
    resp = make_response(render_template("index.html"))
    return resp
@app.route("/band", methods=["GET"])
def page_bandlist():
    resp = make_response(render_template("index.html"))
    return resp
@app.route("/band/detail", methods=["GET"])
def page_bandlist():
    resp = make_response(render_template("index.html"))
    return resp
@app.route("/gateway", methods=["GET"])
def page_bandlist():
    resp = make_response(render_template("index.html"))
    return resp
@app.route("/gateway/detail", methods=["GET"])
def page_bandlist():
    resp = make_response(render_template("index.html"))
    return resp
@app.route("/user", methods=["GET"])
def page_bandlist():
    resp = make_response(render_template("index.html"))
    return resp
@app.route("/user/detail", methods=["GET"])
def page_bandlist():
    resp = make_response(render_template("index.html"))
    return resp
@app.route("/log", methods=["GET"])
def page_bandlist():
    resp = make_response(render_template("index.html"))
    return resp
