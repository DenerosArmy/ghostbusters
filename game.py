from threading import Thread
from Queue import Queue, Empty
import time
from utils import *
import json
import distribution

class GameState(object):
    def __init__(self, width, height,
                 origin=(37.484724,-122.148309),
                 x_dir=(37.484315,-122.147958),
                 y_dir=(37.484911,-122.147929)):
        self.players = []
        self.probability_cloud = {}
        self.add_player("Player1")
        self.ghost_cloud = {}
        self.ghost_cloud["Ghost1"] = distribution.Distribution()
        self.receiving = False
        self.simp_to_geo = transform_mtx(width, height, origin, x_dir, y_dir)
        self.geo_to_simp = inverse(self.simp_to_geo)
        self.queue = Queue()
        self.thread = Thread(target=self.run_thread)
        self.thread.daemon = True # thread dies with the program
        self.thread.start()

    def pt_to_geo(self, pt):
        apply_transform_to_point(self.simp_to_geo, pt)

    def pt_to_simp(self, pt):
        apply_transform_to_point(self.geo_to_simp, pt)

    def angle_to_geo(self, angle):
        return 0.0

    def angle_to_simp(self, angle):
        return 0.0

    def add_player(self, name):
        self.players.append(name)
        self.player_cloud[name] = distribution.Distribution()

    def push(self, timestamp, msg, callback):
        #self.process(timestamp, msg, callback)
        self.queue.put((timestamp, msg, callback))

    def run_thread(self):
        while True:
            timestamp, msg, callback = self.queue.get()
            if time.time() - timestamp > 1.0:
                continue # Ignore out-of-date data
            self.process(timestamp, msg, callback)

    def process(self, timestamp, msg, callback):
        contents = json.loads(msg)
        dist = self.probability_cloud.values()[0]
        dist.update(contents["args"])
        print "Received message", msg

        if contents["action"] == "compass":
            args = [0.25, 0.25, 0.25, 0.25]
        else:
            args = content["args"][0], content["args"][1]
        res = {"action": contents["action"], "args": args}
        callback(json.dumps(res))
