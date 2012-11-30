import random
import logging

def is_valid_location(loc):
    return True # placeholder
def get_random_location():
    return random.random(), random.random()

def time_update(particle):
    """Randomly move a particle: corresponds to time updates of ghosts"""
    return particle

def observe(particle, data):
    return 1.0 # P(data | particle)

class Distribution(object):
    def __init__(self, num_particles=500, initialization_function=get_random_location, transition_function=time_update, emission_function=observe):
        self.num_particles = num_particles
        self.initialization_function = initialization_function
        self.transition_function = transition_function
        self.emission_function = emission_function
        self.initialize_randomly()

    def resample(self, particles, weights, num_particles=None):
        if num_particles is None:
            num_particles = self.num_particles
        total = sum(weights)
        if total == 0:
            return None
        rnd = [random.random() * total for _ in range(num_particles)]
        new_particles = [None for _ in range(num_particles)]
        for wi, w in enumerate(weights):
            for ri in range(len(rnd)):
                if rnd[ri] < 0:
                    continue
                rnd[ri] -= w
                if rnd[ri] < 0:
                    new_particles[ri] = particles[wi]
        return new_particles

    def initialize_randomly(self):
        self.particles = [self.initialization_function() for _ in range(self.num_particles)]

    def tick(self):
        self.particles = map(self.transition_function, self.particles)

    def update(self, data):
        self.particles = self.resample(self.particles, map(lambda particle: self.emission_function(particle, data), self.particles))
        if self.particles is None:
            self.initialize_randomly()
            new_particles = self.resample(self.particles, map(lambda particle: self.emission_function(particle, data), self.particles))
            if new_particles is None:
                logging.error("Cannot update probability distribution due to impossible observations")
            else:
                self.particles = new_particles
