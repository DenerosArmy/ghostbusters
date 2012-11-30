from websocket import create_connection
import json

def connect():
    global ws
    ws = create_connection("ws://0.0.0.0:9000/data")

def compass(x=0.0, y=0.0, acc=0.0, heading=0.0):
    data = {"action": "compass", "args": [x, y, acc, heading]}
    ws.send(json.dumps(data))

def ghost(x=0.0, y=0.0, acc=0.0, heading=0.0):
    ws = create_connection("ws://0.0.0.0:9000/data")
    data = {"action": "compass", "args": [x, y, acc, heading]}
    ws.send(json.dumps(data))

def test():
    connect()
    compass()
    print repr(ws.recv())
