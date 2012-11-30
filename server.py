#!/usr/bin/env python
import tornado
import tornado.web
import tornado.websocket
import tornado.options

import os

import json
import uuid

import argparse

import logging
import time 
import game
logger = logging.getLogger('gateway')

args = None

def parse_args():
    global args
    static_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    parser = argparse.ArgumentParser(description='Gateway server')

    parser.add_argument('-v', '--verbose', help='verbose logging', action='store_true')

    parser.add_argument('-s', '--static-path', help='path for static files [default: %(default)s]', default=static_path)

    parser.add_argument('-p', '--listen-port', help='port to listen on [default: %(default)s]', default=9000, type=int, metavar='PORT')
    parser.add_argument('-i', '--listen-interface', help='interface to listen on. [default: %(default)s]', default='0.0.0.0', metavar='IFACE')

    args = parser.parse_args()
    
    
connections = set()
 
class DataHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print "Adding player ", self.player_num
        connections.add(self)
        game_state.add_player(self.player_num, self)
        return None

    def on_message(self, msg):
        game_state.push(self.player_num, time.time(), msg, self.send)
    
    def send(self,msg):
        if self in connections:
            self.write_message(msg) 

    def on_close(self):
        connections.remove(self)

class DataHandler0(DataHandler):
    player_num = 0

class DataHandler1(DataHandler):
    player_num = 1

class StatusDataHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print "Moving into endgame: opening status"

    def on_message(self, msg):
        game_state.push_status(msg, self.send)

    def send(self, msg):
        if self in connections:
            self.write_message(msg)

    def on_close(self):
        connections.remove(self)

def main():
    global logger
    global game_state 
    game_state = game.GameState(1,1)
    #tornado.options.parse_command_line()

    parse_args()

    if args.verbose:
        tornado.options.enable_pretty_logging()
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

    application = tornado.web.Application([
        (r"/data0", DataHandler0),
        (r"/data1", DataHandler1),
        (r"/status", StatusDataHandler),
    ],
    )

    print "Listening on %s:%s" % (args.listen_interface, args.listen_port)
    application.listen(args.listen_port, args.listen_interface)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
