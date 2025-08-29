print ("module [backend] loaded")
import os
import platform
import logging

from flask_cors import CORS
from flask_sqlalchemy import get_debug_queries
from flask import Flask, render_template, make_response
from flask_restless import APIManager
from flask_socketio import SocketIO
from backend.server_configuration.appConfig import *
from flask_mqtt import Mqtt
from flask import send_from_directory

app = Flask(__name__
            , template_folder=os.getcwd()+'/efwb-frontend/dist'
            , static_folder=os.getcwd()+'/efwb-frontend/dist/static'
            , static_url_path='/admin/static')


cors = CORS(app, resources={r"/api/*": {"origins": "*"},
                            r"/socket.io/*": {
                            "origins": "*",
                            "methods": ["GET", "POST"],
                            "allow_headers": ["token"]
                            }
                        }, max_age=86400)

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
mqtt.subscribe('/DT/eHG4/naas/post/sync')
mqtt.subscribe('/DT/eHG4/naas/post/async')
mqtt.subscribe('/DT/eHG4/naas/WEATHER/GET')
mqtt.subscribe('/DT/eHG4/naas/INFO/GET')
# mqtt.subscribe('/DT/eHG4/post/connectcheck')
mqtt.subscribe('/DT/eHG4/naas/Status/Band_Events_Data')

# New CHU
mqtt.subscribe('/DT/eHG4/naas/GPS/Location')

manager = APIManager(app, flask_sqlalchemy_db=DBManager.db)

# socket init
socketio = SocketIO(app,
                    cors_allowed_origins="*",
                    async_mode='gevent',
                    ping_timeout=60,
                    ping_interval=25,
                    # logger=True,          # 로깅 활성화
                    # engineio_logger=True  # Engine.IO 로깅 활성화
                    )

@app.route("/admin/", methods=["GET"])
def admin_index():
    resp = make_response(render_template("index.html"))
    return resp

@app.route("/admin/band/", methods=["GET"])
def admin_band():
    resp = make_response(render_template("index.html"))
    return resp

@app.route("/admin/band/detail/", methods=["GET"])
def admin_band_detail():
    resp = make_response(render_template("index.html"))
    return resp

# @app.route("/admin/gateway/", methods=["GET"])
# def admin_gateway():
#     resp = make_response(render_template("index.html"))
#     return resp

# @app.route("/admin/gateway/detail/", methods=["GET"])
# def admin_gateway_detail():
#     resp = make_response(render_template("index.html"))
#     return resp

@app.route("/admin/user/", methods=["GET"])
def admin_user():
    resp = make_response(render_template("index.html"))
    return resp

@app.route("/admin/user/detail/", methods=["GET"])
def admin_user_detail():
    resp = make_response(render_template("index.html"))
    return resp

@app.route("/admin/log/", methods=["GET"])
def admin_log():
    resp = make_response(render_template("index.html"))
    return resp

@app.route("/admin/<path:path>")
def admin_static(path):
    return send_from_directory('/home/ubuntu/admin/efwb_admin/efwb-frontend/dist/static', path)

from backend.api.api_create import *
#from backend.api.mqtt import *

server = db.session.query(Server).first()
if server.start == 0 :
    db.session.query(Server).filter(Server.id == 1).update(dict(start=1))
    db.session.commit()
  
else :
    db.session.query(Server).filter(Server.id == 1).update(dict(start=0))
    db.session.commit()

def init_background_tasks(socketio):
    from .api.mqtt import background_done  # 순환 참조 방지 위해 지연 임포트
    background_done.clear()  # 초기화 시작 → MQTT 잠금

    def run_all_background():
        # 각 백그라운드 태스크를 비동기적으로 개별 실행
        socketio.start_background_task(start_disconnect_checker)
        socketio.start_background_task(start_publish_weather_mqtt_to_bands)
        #socketio.start_background_task(start_weather_warning_mqtt_publish_checker)

        # 초기화 후 즉시 MQTT 메시지 처리 허용
        background_done.set()
        print("백그라운드 태스크 시작 → MQTT 메시지 처리 가능")

    socketio.start_background_task(run_all_background)

init_background_tasks(socketio)


