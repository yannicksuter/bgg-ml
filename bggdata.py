#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json, re, string
from boardgamegeek2 import BGGClient
from lxml import html
import requests

class Game(object):
    def __init__(self, id = 0, name = "", overall_rank = None, min_players = None, max_players = None, min_playing_time = None, max_playing_time = None):
        self.id = id
        self.name = name
        self.overall_rank = overall_rank
        self.min_players = min_players
        self.max_players = max_players
        self.min_playing_time = min_playing_time
        self.max_playing_time = max_playing_time

    def set(self, values):
        for k, v in values.items():
            setattr(self, k, v)
        return self

    def print(self):
        print(" == Details: [{}] {} ==".format(self.id, self.name))
        for key, value in self.__dict__.items():
            if key is not "id" and key is not "name" and value is not None:
                print(" {} : {}".format(key, value))
        # print(self.id, self.name, self.min_players, self.max_players, self.min_playing_time, self.max_playing_time)


class GameCollection(object):
    def __init__(self, username):
        self.username = username
        self.cache_filename = "data/%s_owned_collection.cache" % self.username
        self.owned_games = None

    def load(self, force_reload = False):
        if not self.username:
            raise Exception("ERROR: no username was defined, please use --user=USERNAME to provide reference.")

        if not force_reload:
            try:
                with open(self.cache_filename, "r") as owned:
                    self.owned_games = []
                    for line in owned.readlines():
                        self.owned_games.append(Game().set(json.loads(line)))
                print("Collection loaded: %d games (cache)" % len(self.owned_games))
                return
            except:
                print("Cached file not found. ({})".format(self.cache_filename))


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
                with open(self.cache_filename, "w") as owned:
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

class GameRepository(object):
    def __init__(self):
        self.games = None
        self.cache_filename = "data/game_repository.cache"

    def normalize(self, text):
        if text is None:
            return ''
        s = ''.join(re.compile(r'\W+', re.UNICODE).split(text)).lower()
        return filter(lambda x: x in set(string.printable), s)


    def load(self, force_reload=False):
        self.games = []
        try:
            self.loadCache(self.cache_filename, self.games)
            print("Repository loaded: %d games (cache)" % len(self.games))
        except:
            print("Cached file not found. ({})".format(self.cache_filename))

        if self.games is None or force_reload:
            entry_counter = 0
            url_paged = "https://boardgamegeek.com/browse/boardgame/page/{}?sort=rank"
            for page in range(1,2):
                r = re.compile('/boardgame/(\d+)')
                dom = html.fromstring(requests.get(url_paged.format(page)).text)
                rows = dom.cssselect('tr#row_')
                if rows is not None:
                    for row in rows:
                        try:
                            entry_exp_rank = entry_counter+1
                            entry_link = row.cssselect('td div a')[0].attrib['href']
                            entry_title = row.cssselect('td div a')[0].text
                            entry_id = int(r.search(entry_link).group(1))
                            entry_counter += 1
                            # print("#{}:{} {} ({})".format(entry_exp_rank, entry_id, entry_title, entry_link))
                            self.games.append(Game(entry_id, entry_title, overall_rank=entry_exp_rank))
                        except:
                            pass
            print("Repository loaded: %d games (web)" % len(self.games))
            self.dumpCache(self.cache_filename, self.games)

    def loadCache(self, filename, list):
        try:
            with open(filename, "r") as input_file:
                for line in input_file.readlines():
                    list.append(Game().set(json.loads(line)))
            print("{} entries loaded from cache ({}).".format(len(list), filename))
        except:
            pass


    def dumpCache(self, filename, list):
        try:
            if list:
                with open(filename, "w") as output_file:
                    for entry in list:
                        output_file.write(json.dumps(entry.__dict__).encode(encoding='UTF-8', errors='strict').decode('utf-8')+"\n")
        except:
            pass

    def getById(self, id):
        for game in self.games:
            if game.id == id:
                return game
        return None

    # def loadDetails(self, force_reload=False):
        # game_ids = [82222]
        # self.bgg = BGGClient()
        # for details in self.bgg.game_list(game_ids):
        #     game = self.getById(details.id)
        #     game.rank_overall = details.bgg_rank
        # mechanics
        # categories
        # families
        # print(details)
