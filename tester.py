from websocket import create_connection
import json

from game import GameState
from utils import *

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

def test_coord():
    state = GameState(1,1)
    pt = [0.5, 0.5]
    state.pt_to_geo(pt)
    print pt
    pt = [37.48459, -122.147926]
    state.pt_to_simp(pt)
    print pt
