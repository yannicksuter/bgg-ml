#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from boardgamegeek import BGGClient

class Game(object):
    def __init__(self, id = 0, name = "", min_players = 0, max_players = 0, min_playing_time = 0, max_playing_time = 0):
        self.id = id
        self.name = name
        self.min_players = min_players
        self.max_players = max_players
        self.min_playing_time = min_playing_time
        self.max_playing_time = max_playing_time

    def set(self, values):
        for k, v in values.items():
            setattr(self, k, v)
        return self

    def print(self):
        print(self.id, self.name, self.min_players, self.max_players, self.min_playing_time, self.max_playing_time)

class GameCollection(object):
    def __init__(self, username):
        self.username = username
        self.owned_games = None

    def load(self, force_web = False):
        if not self.username:
            raise Exception("ERROR: no username was defined, please use --user=USERNAME to provide reference.")

        if not force_web:
            try:
                with open("data/%s_owned_collection.cache" % self.username, "r") as owned:
                    self.owned_games = []
                    for line in owned.readlines():
                        self.owned_games.append(Game().set(json.loads(line)))
                print("Collection loaded: %d games (cache)" % len(self.owned_games))
                return
            except:
                print("Cached files not found.")


        self.bgg = BGGClient()
        owned_games  = self.bgg.collection(self.username, own=True)
        if owned_games:
            self.owned_games = []
            for game in owned_games.items:
                self.owned_games.append(Game(game.id, game.name, game.min_players, game.max_players, game.min_playing_time, game.max_playing_time))
            print("Collection loaded: %d games (web)" % len(self.owned_games))
            self.dumpCache()

    def dumpCache(self):
        try:
            if self.owned_games:
                with open("data/%s_owned_collection.cache" % self.username, "w") as owned:
                    for game in self.owned_games:
                        owned.write(json.dumps(game.__dict__).encode(encoding='UTF-8', errors='strict').decode('utf-8')+"\n")
        except:
            pass

    def show(self):
        if self.owned_games:
            for game in self.owned_games:
                game.print()
        else:
            print("no games loaded for %s" % self.username)