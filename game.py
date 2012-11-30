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
                 origin=(37.483347,-122.149692),
                 y_dir=(37.483656,-122.149366),
                 x_dir=(37.483147,-122.149349)):
        self.player_cloud = {}
        self.player_angles = {}
        self.player_connections = {}
        self.player_speeds = {}
        self.ghost_cloud = {}
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
        self.plotthread = Thread(target=self.plot_particles)
        self.plotthread.daemon = True
        self.plotthread.start()

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
        sigma = 0.3 # TODO: better parameter that reflects actual GPS accuracy
        probability = 1.0 / (sigma * math.sqrt(2 * math.pi)) * math.exp(-0.5 * distance_squared / sigma**2) # normal distribution
        return probability

    def player_transition(self, name, particle):
        x, y = None, None
        angle = self.player_angles[name]
        speed = self.player_speeds[name]
        travel_distance = speed * 8 # TODO: better parameter that reflects reality and time
        random_distance = 0.02
        while not distribution.is_valid_location((x, y)):
            distance = random.uniform(0.0, travel_distance)
            dx = distance * math.cos(math.radians(angle))
            dy = distance * math.sin(math.radians(angle))
            x = particle[0] + dx + random.uniform(-random_distance, random_distance)
            y = particle[1] + dy + random.uniform(-random_distance, random_distance)
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


    def player_ghost_angles(self, player):
        ghost_dist = self.ghost_cloud.values()[0]
        player_dist = self.player_cloud[player]
        upsampling_factor = 2
        distance_limit = 0.5
        angles = []
        for ghost_loc in ghost_dist.particles:
            for _ in range(upsampling_factor):
                player_loc = player_dist.sample()
                dx = ghost_loc[0] - player_loc[0]
                dy = ghost_loc[1] - player_loc[1]
                if dx**2 + dy**2 > distance_limit**2:
                    angles.append(None)
                    continue
                angle = math.degrees(math.atan2(dy, dx))
                if angle < 0.0:
                    angle += 360.0
                angles.append(angle)
        return angles

    def player_ghost_angles_geo(self, player):
        angles = map(self.angle_to_geo, self.player_ghost_angles(player))
        res = [0, 0, 0, 0, 0]
        for angle in angles:
            if angle is None:
                res[4] += 1
                continue
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
        if angle is None:
            return None
        return (90 - (angle - self.geo_to_simp_angle)) % 360

    def angle_to_geo(self, angle):
        if angle is None:
            return None
        return (angle - self.geo_to_simp_angle) % 360

    def add_player(self, name, connection):
        self.player_cloud[name] = distribution.Distribution(emission_function=self.player_observation, transition_function=lambda x: self.player_transition(name, x))
        self.player_angles[name] = 0.0
        self.player_connections[name] = connection
        self.player_speeds[name] = 0.0

    def push(self, player, timestamp, msg, callback):
        #self.process(timestamp, msg, callback)
        contents = json.loads(msg)
        if contents["action"] == "snap":
            self.snap_queue.put((player, timestamp, msg, callback))
        else:
            self.compass_queue.put((player, timestamp, msg, callback))

    def run_thread(self):
        self.time_since_tick = time.time()
        while True:
            if not self.snap_queue.empty():
                player, timestamp, msg, callback = self.snap_queue.get()
                if time.time() - timestamp < 1.0: # Ignore out-of-date data
                    self.process(player, timestamp, msg, callback)
            elif not self.compass_queue.empty():
                player, timestamp, msg, callback = self.compass_queue.get()
                if time.time() - timestamp < 1.0: # Ignore out-of-date data
                    print "processing compass ", msg
                    self.process(player, timestamp, msg, callback)
            else:
                if time.time() - self.time_since_tick > 1.0:
                    # Tick the distribution every second
                    print "tick"
                    for dist in self.player_cloud.values():
                        dist.tick()
                    ghost_dist = self.ghost_cloud.values()[0]
                    ghost_dist.tick()
                    self.time_since_tick = time.time()

    def plot_particles(self, title="Untitled"):
        ghost_dist = self.ghost_cloud.values()[0]
        colors = {0: 'bo', 1: 'go'}
        try:
            print "plotting"
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import shutil
            plt.plot([p[0] for p in ghost_dist.particles], [p[1] for p in ghost_dist.particles], 'ro')
            plt.show()
            while True:
                plt.clf()
                time.sleep(1)
                plt.plot([p[0] for p in ghost_dist.particles], [p[1] for p in ghost_dist.particles], 'ro')
                for name, dist in self.player_cloud.items():
                    plt.plot([p[0] for p in dist.particles], [p[1] for p in dist.particles], colors[name])
                plt.axis([0, 1, 0, 1])
                print "new plot generated"
                plt.savefig("figure_.png")
                shutil.move("figure_.png", "figure.png")
        except ImportError:
            pass

    def process(self, player, timestamp, msg, callback):
        print "Received message", msg, "for player", player
        contents = json.loads(msg)
        contents["args"] = eval(contents["args"])
        player_data = contents["args"][:]
        player_data[0], player_data[1] = self.pt_to_simp(player_data[0:2])
        player_data[3] = self.angle_to_simp(player_data[3])
        dist = self.player_cloud[player]
        dist.tick()
        dist.update(player_data)
        print "Centroid", dist.centroid()

        self.player_angles[player] = player_data[3]
        self.player_speeds[player] = player_data[4]
        print self.player_speeds
        if contents["action"] == "compass":
            args = self.player_ghost_angles_geo(player)
        else:
            ghost_dist = self.ghost_cloud.values()[0]
            print "Ghost centroid before", ghost_dist.centroid()
            print "Ghost angles before:", self.player_ghost_angles_geo(player)
            ghost_location = self.measure_ghost(player_data)
            data = dist, player_data, ghost_location
            ghost_dist.update(data)
            print "Ghost centroid after", ghost_dist.centroid()
            print "Ghost angles after:", self.player_ghost_angles_geo(player)
            if ghost_location is not None:
                args = self.pt_to_geo(list(ghost_location))
                for player_num, conn in self.player_connections.items():
                    if player_num != player:
                        conn.send(json.dumps({"action": "notify", "args": args}))
            else:
                args = [0.0, 0.0]
        res = {"action": contents["action"], "args": args}
        callback(json.dumps(res))
