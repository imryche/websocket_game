import random
import json

import tornado.httpserver
import tornado.ioloop
import tornado.websocket
import tornado.options
from uuid import uuid4

from tornado.options import define, options
define('port', default=8000, help='run on the given port', type=int)

class Application(tornado.web.Application):
    def __init__(self):
        self.world = GameWorld(640, 480)

        handlers = [
            (r'/', IndexHandler),
            (r'/game', GameSocketHandler)
        ]

        settings = dict(
            debug=True
        )
        super(Application, self).__init__(handlers, **settings)

class Player(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def move_to(x, y):
        self.x = x
        self.y = y


class GameWorld(object):
    players = {}

    def __init__(self, width, height):
        self.width = width
        self.height = height

    def get_world_size(self):
        return self.width, self.height

    def add_player(self, player, name):
        self.players[name] = player

    def remove_player(self, name):
        del self.players[name]

    def move_player(self, name, x, y):
        self.players[name].x = x
        self.players[name].y = y

    def get_world_state(self):
        return json.dumps({str(player[0]): [player[1].x, player[1].y] for player in self.players.iteritems()})


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class GameSocketHandler(tornado.websocket.WebSocketHandler):
    waiters = set()

    def send_updates(self, world_state):
        for waiter in self.waiters:
            waiter.write_message(world_state)

    def open(self):
        GameSocketHandler.waiters.add(self)

    def on_close(self):
        GameSocketHandler.waiters.remove(self)

    def on_message(self, raw_data):
        data = json.loads(raw_data);
        action = data['action']
        name = data['name']
        pos = data['pos']

        if action == 'init':
            player = Player(100, 100)
            self.application.world.add_player(player, name)
        elif action == 'destroy':
            self.application.world.remove_player(name)
        elif action == 'move':
            self.application.world.move_player(name, pos[0], pos[1])

        self.send_updates(self.application.world.get_world_state())


if __name__ == '__main__':
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()
