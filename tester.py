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
    pt = [1, 0]
    state.pt_to_geo(pt)
    print "x limit ", pt
    pt = [0, 1]
    state.pt_to_geo(pt)
    print "y limit ", pt

test_coord()

def test_angle():
    state = GameState(1,1)
    print "Convert 45 to simple ", state.angle_to_simp(45)
    print "Convert 45 to geo ", state.angle_to_geo(45)
    print "Convert 90 to simple ", state.angle_to_simp(90)
    print "Convert 90 to geo ", state.angle_to_geo(90)
    print "Convert 270 to simple ", state.angle_to_simp(270)
    print "Convert 270 to geo ", state.angle_to_geo(270)

test_angle()
