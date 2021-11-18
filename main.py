print("module [app] loaded")
import os
from backend import app, socketio


if __name__ == "__main__":
    port = int(os.environ.get('PORT', app.config['BIND_PORT']))
    socketio.run(app, host="0.0.0.0", port=port)
    
    
