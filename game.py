from math import *
from threading import Thread
from Queue import Queue, Empty
import time
from utils import *

class GameState(object):
    def __init__(self, width, height,
                 origin=(37.484724,-122.148309),
                 x_dir=(37.484315,-122.147958),
                 y_dir=(37.484911,-122.147929)):
        self.players = []
        self.probability_cloud = {}
        self.receiving = False
        self.simp_to_geo = transform_mtx(width, height, origin, x_dir, y_dir)
        self.geo_to_simp = inverse(self.simp_to_geo)
        self.queue = Queue()
        self.thread = Thread(target=self.run_thread)
        self.thread.daemon = True # thread dies with the program
        self.thread.start()

    def add_player(self, name):
        self.players.append(name)
        self.probability_cloud[name] = ProbabilityCloud()

    def push(self, timestamp, msg, callback):
        self.queue.put((timestamp, msg, callback))

    def run_thread(self):
        while True:
            timestamp, msg, callback = self.queue.get()
            if time.time() - timestamp > 1.0:
                continue # Ignore out-of-date data
            print "Received message", msg
            callback("")
