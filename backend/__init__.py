print ("module [backend] loaded")

from flask_cors import CORS
from flask_sqlalchemy import get_debug_queries
import os
import platform
import paho.mqtt.client as mqtt
from flask import Flask, render_template, make_response
from flask_restless import APIManager
from flask_socketio import SocketIO
from backend.server_configuration.appConfig import *
from flask_mqtt import Mqtt

# app = Flask(__name__)

app = Flask(__name__
            , template_folder=os.getcwd()+'/frontend/dist'
            , static_folder=os.getcwd()+'/frontend/dist/static'
            , static_url_path='/static')


cors = CORS(app, resources={r"/api/*": {"origins": "*"}}, max_age=86400)
app.config['MQTT_BROKER_URL'] = "t-vsm.com"
app.config['MQTT_BROKER_PORT'] = 18831



cur_system = platform.system()
if cur_system == "Windows":
    app.config.from_object(DevelopmentConfig)
else:
    app.config.from_object(ProductionConfig)


# table
# from backend_model import *
from backend.db.database import DBManager
DBManager.init(app)


# api
mqtt = Mqtt(app)
manager = APIManager(app, flask_sqlalchemy_db=DBManager.db)
socketio = SocketIO(app, cors_allowed_origins="*", engineio_logger=False)

mqtt.subscribe('/efwb/sync')
from backend.api.api_create import *
from backend.api.api_band import *


@app.route("/", methods=["GET"])
def page_index():
    resp = make_response(render_template("index.html"))
    return resp