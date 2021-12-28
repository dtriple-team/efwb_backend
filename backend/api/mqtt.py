from backend import app, socketio, mqtt

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    print("mqtt connect")