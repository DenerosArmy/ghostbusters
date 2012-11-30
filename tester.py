from websocket import create_connection
import json

from game import GameState
from utils import *

def connect():
    global ws0, ws1
    ws0 = create_connection("ws://0.0.0.0:9000/data0")
    ws1 = create_connection("ws://0.0.0.0:9000/data1")

def compass(x=37.484724, y=-122.148309, acc=0.0, heading=108.79):
    data = {"action": "compass", "args": str([x, y, acc, heading])}
    ws0.send(json.dumps(data))
    # ws1.send(json.dumps(data))

def ghost(x=37.484724, y=-122.148309, acc=0.0, heading=108.79):
    data = {"action": "ghost", "args": str([x, y, acc, heading])}
    ws0.send(json.dumps(data))
    # ws1.send(json.dumps(data))

def test():
    connect()
    compass()
    print repr(ws0.recv())
    # print repr(ws1.recv())

def test_coord():
    state = GameState(1,1)
    pt = [1, 0]
    state.pt_to_geo(pt)
    print "x limit ", pt
    pt = [0, 1]
    state.pt_to_geo(pt)
    print "y limit ", pt

def test_angle():
    state = GameState(1,1)
    print "Convert 45 to simple ", state.angle_to_simp(45)
    print "Convert 45 to geo ", state.angle_to_geo(45)
    print "Convert 90 to simple ", state.angle_to_simp(90)
    print "Convert 90 to geo ", state.angle_to_geo(90)
    print "Convert 270 to simple ", state.angle_to_simp(270)
    print "Convert 270 to geo ", state.angle_to_geo(270)
