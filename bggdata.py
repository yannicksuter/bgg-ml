#!/usr/bin/env python
# -*- coding: utf-8 -*-

from boardgamegeek import BGGClient

class GameCollectionItem(object):
    def __init__(self, id, name, min_players, max_players, min_playing_time, max_playing_time):
        self.id = id
        self.name = name
        self.min_players = min_players
        self.max_players = max_players
        self.min_playing_time = min_playing_time
        self.max_playing_time = max_playing_time

    def print(self):
        print(self.id, self.name, self.min_players, self.max_players, self.min_playing_time, self.max_playing_time)

class GameCollection(object):
    def __init__(self, username):
        self.username = username
        self.owned_games = None

    def loadFromWeb(self):
        if not self.username:
            raise Exception("ERROR: no username was defined, please use --user=USERNAME to provide reference.")

        self.bgg = BGGClient()
        owned_games  = self.bgg.collection(self.username, own=True)

        if owned_games:
            self.owned_games = []
            for game in owned_games.items:
                self.owned_games.append(GameCollectionItem(game.id, game.name, game.min_players, game.max_players, game.min_playing_time, game.max_playing_time))
            self.dump()

        return True

    def loadFromDump(self):
        try:
            with open("%s_owned_collection.cache" % self.username) as owned:
                for line in owned.readlines():
                    print(line)
        except:
            print("Cached files not found - trying to fetch them online.")
            return self.loadFromWeb()

        return True

    def dump(self):
        pass

    def show(self):
        if self.owned_games:
            for game in self.owned_games:
                game.print()
        else:
            print("no games loaded for %s" % self.username)