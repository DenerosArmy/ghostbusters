import json
from math import sin, cos, tan, atan, degrees, radians
from Queue import Queue, Empty
from threading import Thread
import time

from utils import *
import distribution
import math
import random

class GameState(object):
    def __init__(self, width, height,
                 origin=(37.484724,-122.148309),
                 x_dir=(37.484315,-122.147958),
                 y_dir=(37.484911,-122.147929)):
        self.players = []
        self.player_cloud = {}
        self.ghost_cloud = {}
        self.add_player("Player1")
        self.ghost_cloud["Ghost1"] = distribution.Distribution(emission_function=self.ghost_observation)

        #rotate a geo angle CW this many degrees to get simple
        self.geo_to_simp_angle = degrees(math.atan2((y_dir[1]-origin[1]),(y_dir[0]-origin[0])))
        self.simp_to_geo = transform_mtx(width, height, origin, x_dir, y_dir)
        self.geo_to_simp = inverse(self.simp_to_geo)

        self.receiving = False
        self.compass_queue = Queue()
        self.snap_queue = Queue()

        self.thread = Thread(target=self.run_thread)
        self.thread.daemon = True # thread dies with the program
        self.thread.start()
        self.time_since_tick = time.time()

    def measure_ghost(self, data):
        angle_limit = 45.0
        distance_limit = 1.0
        ghost_dist = self.ghost_cloud.values()[0]
        gx, gy = ghost_dist.sample()
        px, py = data[0:2]
        measured_angle = math.degrees(math.atan2(gy-py, gx-px))
        if measured_angle < 0:
            measured_angle += 360
        phone_angle = data[3]
        if angle_limit < abs(measured_angle - phone_angle) < 360.0-angle_limit:
            return None
        elif (gx-px)**2 + (gy-py)**2 > distance_limit**2:
            return None
        else:
            return gx, gy

    def player_observation(self, particle, data):
        x, y = particle
        ax, ay = data[0:2]
        distance_squared = (x-ax)**2 + (y-ay)**2
        sigma = 0.9 # TODO: better parameter that reflects actual GPS accuracy
        probability = 1.0 / (sigma * math.sqrt(2 * math.pi)) * math.exp(-0.5 * distance_squared / sigma**2) # normal distribution
        return probability

    def player_transition(self, particle):
        x, y = None, None
        travel_distance = 0.05 # TODO: better parameter that reflects reality and time
        while not distribution.is_valid_location((x, y)):
            x = particle[0] + random.uniform(-0.5, 0.5) * travel_distance * 2.0
            y = particle[1] + random.uniform(-0.5, 0.5) * travel_distance * 2.0
        return x, y

    def ghost_observation(self, particle, data):
        angle_limit = 45.0
        distance_limit = 1.0

        gx, gy = particle
        player_dist, player_vect, ghost_loc = data
        player_angle = player_vect[3]
        total = 0
        samples = 10
        for _ in range(samples):
            px, py = player_dist.sample()
            if (px - gx)**2 + (py-gy)**2 > distance_limit**2:
                continue
            measured_angle = math.degrees(math.atan2(gy-py, gx-px))
            if measured_angle < 0:
                measured_angle += 360
            if angle_limit < abs(measured_angle - player_angle) < 360.0-angle_limit:
                continue
            total += 1
        if ghost_loc is not None:
            return float(total)/samples
        else:
            return 1.0 - float(total)/samples


    def player_ghost_angles(self):
        ghost_dist = self.ghost_cloud.values()[0]
        player_dist = self.player_cloud.values()[0]
        upsampling_factor = 2
        angles = []
        for ghost_loc in ghost_dist.particles:
            for _ in range(upsampling_factor):
                player_loc = player_dist.sample()
                dx = ghost_loc[0] - player_loc[0]
                dy = ghost_loc[1] - player_loc[1]
                angle = math.degrees(math.atan2(dy, dx))
                if angle < 0.0:
                    angle += 360.0
                angles.append(angle)
        return angles

    def player_ghost_angles_geo(self):
        angles = map(self.angle_to_geo, self.player_ghost_angles())
        res = [0, 0, 0, 0]
        for angle in angles:
            assert angle >= 0, "Internal error: negative angles"
            if angle < 90:
                res[0] += 1
            elif angle < 180:
                res[1] += 1
            elif angle < 270:
                res[2] += 1
            else:
                assert angle < 360, "Internal error: angle greater than 360 degrees"
                res[3] += 1
        res = [x*1.0/len(angles) for x in res]
        return res

    def pt_to_geo(self, pt):
        apply_transform_to_point(self.simp_to_geo, pt)
        return pt

    def pt_to_simp(self, pt):
        apply_transform_to_point(self.geo_to_simp, pt)
        return pt

    def angle_to_simp(self, angle):
        return (angle - self.geo_to_simp_angle) % 360

    def angle_to_geo(self, angle):
        return (angle + self.geo_to_simp_angle) % 360

    def add_player(self, name):
        self.players.append(name)
        self.player_cloud[name] = distribution.Distribution(emission_function=self.player_observation, transition_function=self.player_transition)

    def push(self, timestamp, msg, callback):
        #self.process(timestamp, msg, callback)
        contents = json.loads(msg)
        if contents["action"] == "snap":
            self.snap_queue.put((timestamp, msg, callback))
        else:
            self.compass_queue.put((timestamp, msg, callback))

    def run_thread(self):
        self.time_since_tick = time.time()
        while True:
            if not self.snap_queue.empty():
                timestamp, msg, callback = self.snap_queue.get()
                if time.time() - timestamp < 1.0: # Ignore out-of-date data
                    self.process(timestamp, msg, callback)
            elif not self.compass_queue.empty():
                timestamp, msg, callback = self.compass_queue.get()
                if time.time() - timestamp < 1.0: # Ignore out-of-date data
                    self.process(timestamp, msg, callback)
            else:
                if time.time() - self.time_since_tick > 1.0:
                    # Tick the distribution every second
                    print "tick"
                    dist = self.player_cloud.values()[0]
                    dist.tick()
                    ghost_dist = self.ghost_cloud.values()[0]
                    ghost_dist.tick()
                    self.time_since_tick = time.time()

    def process(self, timestamp, msg, callback):
        print "Received message", msg
        contents = json.loads(msg)
        contents["args"] = eval(contents["args"])
        player_data = contents["args"][:]
        player_data[0], player_data[1] = self.pt_to_simp(player_data[0:2])
        player_data[3] = self.angle_to_simp(player_data[3])
        dist = self.player_cloud.values()[0]
        dist.update(player_data)
        print "Centroid", dist.centroid()

        if contents["action"] == "compass":
            args = self.player_ghost_angles_geo()
        else:
            ghost_dist = self.ghost_cloud.values()[0]
            print "Ghost centroid before", ghost_dist.centroid()
            print "Ghost angles before:", self.player_ghost_angles_geo()
            ghost_location = self.measure_ghost(player_data)
            data = dist, player_data, ghost_location
            ghost_dist.update(data)
            print "Ghost centroid after", ghost_dist.centroid()
            print "Ghost angles after:", self.player_ghost_angles_geo()
            if ghost_location is not None:
                args = self.pt_to_geo(list(ghost_location))
            else:
                args = None
        res = {"action": contents["action"], "args": args}
        callback(json.dumps(res))
