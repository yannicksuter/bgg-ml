#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json, re, string
from boardgamegeek2 import BGGClient
from lxml import html
import requests
import progressbar
from tqdm import tqdm
# from progress.bar import Bar

def loadCache(filename, obj_list):
    assert obj_list is not None
    try:
        with open(filename, "r") as input_file:
            for line in input_file.readlines():
                obj_list.append(Game().set(json.loads(line)))
        print("{} entries loaded from cache ({}).".format(len(obj_list), filename))
    except:
        pass


def dumpCache(filename, obj_list):
    assert obj_list is not None
    try:
        with open(filename, "w") as output_file:
            for entry in obj_list:
                output_file.write(
                    json.dumps(entry.__dict__).encode(encoding='UTF-8', errors='strict').decode('utf-8') + "\n")
    except:
        pass

def normalize(text):
    if text is None:
        return ''
    s = ''.join(re.compile(r'\W+', re.UNICODE).split(text)).lower()
    return filter(lambda x: x in set(string.printable), s)

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

class Game(object):
    def __init__(self, id = 0, name = "", overall_rank = None, min_players = None, max_players = None, min_playing_time = None, max_playing_time = None):
        self.id = id
        self.name = name
        self.overall_rank = overall_rank
        self.expansion = None
        self.expands = None
        self.minplayers = min_players
        self.maxplayers = max_players
        self.minplaytime = min_playing_time
        self.maxplaytime = max_playing_time

    def set(self, values):
        for k, v in values.items():
            if k in self.__dict__.keys():
                setattr(self, k, v)
        return self

    def isValid(self):
        return (self.id != 0 and self.name != "")

    def setBGGGame(self, bgg_game):
        self.set(bgg_game._data)
        for rank in bgg_game.ranks:
            if rank.id == 1:
                self.overall_rank = rank.value
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
        self.bgg = BGGClient()

    def load(self, repository, force_reload = False):
        if not self.username:
            raise Exception("ERROR: no username was defined, please use --user=USERNAME to provide reference.")

        game_ids = []
        self.owned_games = []
        try:
            with open(self.cache_filename, "r") as owned:
                self.owned_games = []
                for line in owned.readlines():
                    g_json = json.loads(line)
                    game_ids.append(g_json['id'])
        except:
            print("Cached file not found. ({})".format(self.cache_filename))

        if len(self.owned_games) == 0 or force_reload:
            game_ids = []
            collection  = self.bgg.collection(self.username, own=True)
            if collection:
                for game in collection.items:
                    game_ids.append(game.id)

        self.owned_games = repository.getByIds(game_ids)
        dumpCache(self.cache_filename, self.owned_games)

        print("Collection [owned:{}] loaded: {} games".format(self.username, len(self.owned_games)))

class GameRepository(object):
    def __init__(self):
        self.games = None
        self.cache_filename = "data/game_repository.cache"
        self.bgg = BGGClient()

    def load(self, force_reload=False, max_pages=20):
        self.games = []
        try:
            loadCache(self.cache_filename, self.games)
        except:
            print("Cached file not found. ({})".format(self.cache_filename))

        if len(self.games) == 0 or force_reload:
            entry_counter = 0
            uid_r = re.compile('/boardgame/(\d+)')
            url_paged = "https://boardgamegeek.com/browse/boardgame/page/{}?sort=rank"
            for page in tqdm(range(max_pages), desc="Loading overall-rank games", ncols=100):
                dom = html.fromstring(requests.get(url_paged.format(page+1)).text)
                rows = dom.cssselect('tr#row_')
                if rows is not None:
                    for row in rows:
                        try:
                            entry_exp_rank = entry_counter+1
                            entry_link = row.cssselect('td div a')[0].attrib['href']
                            entry_id = int(uid_r.search(entry_link).group(1))
                            entry_counter += 1
                            self.games.append(Game(entry_id, overall_rank=entry_exp_rank))
                        except:
                            pass
            dumpCache(self.cache_filename, self.games)

        self.validate()
        print("Repository loaded: %d games." % len(self.games))

    def validate(self, retries = 3):
        for run in range(retries):
            invalid_entries = list(filter(lambda x : not x.isValid(), self.games))
            if len(invalid_entries) == 0:
                return
            print("Loading missing game details from BGG [count: {}].".format(len(invalid_entries)))
            for chunk in tqdm(iterable=list(chunks(invalid_entries, 50)), desc="Loading game details (try:{})".format(run+1), ncols=100):
                games = [game.id for game in chunk]
                for res in self.bgg.game_list(games):
                    self.getById(res.id).setBGGGame(res)
            dumpCache(self.cache_filename, self.games)

    def getByIds(self, id_list, load_missing = True):
        if load_missing:
            game_index = [x.id for x in self.games]
            for missing_id in list(filter(lambda x: x not in game_index, id_list)):
                self.games.append(Game(id=missing_id))
            self.validate()
        return list(filter(lambda x: x.id in id_list and x.isValid, self.games))

    def getById(self, id, load_missing = True):
        for game in self.games:
            if game.id == id:
                return game

        result = None
        if load_missing:
            bgg_game = self.bgg.game(game_id=id)
            if bgg_game:
                print("Missing ID={}, loading...".format(id))
                result = Game().setBGGGame(bgg_game)
                self.games.append(result)
        return result
