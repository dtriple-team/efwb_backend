# from flask import Flask
# from flask_socketio import SocketIO
# from flask_cors import CORS
# app = Flask(__name__)

# @app.route("/")
# def hello():
#     return "Hello World!"
# cors = CORS(app, resources={r"/api/*": {"origins": "*"}}, max_age=86400)
# socketio = SocketIO(app, cors_allowed_origins="*", engineio_logger=False)

# if __name__ == "__main__":
#     app.run("0.0.0.0", port=8080)


print("module [app] loaded")
import os
from backend import app, socketio, hello


if __name__ == "__main__":
    port = int(os.environ.get('PORT', app.config['BIND_PORT']))
    socketio.run(app,  host="0.0.0.0", port=port)
    
    
