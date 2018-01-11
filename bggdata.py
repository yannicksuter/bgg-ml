#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json, re, string
from boardgamegeek2 import BGGClient
from lxml import html
import requests
from tqdm import tqdm

def load_cache(filename, obj_list, obj_type=None):
    assert obj_list is not None
    try:
        with open(filename, "r") as input_file:
            for line in input_file.readlines():
                if obj_type:
                    obj_list.append(obj_type().set(json.loads(line)))
                else:
                    obj_list.append(json.loads(line))
        print("{} entries loaded from cache ({}).".format(len(obj_list), filename))
    except Exception as e:
        print("Error: %s" % str(e))

def dump_cache(filename, obj_list):
    assert obj_list is not None
    try:
        with open(filename, "w") as output_file:
            for entry in obj_list:
                output_file.write(
                    json.dumps(entry if type(entry) is dict else entry.__dict__).encode(encoding='UTF-8', errors='strict').decode('utf-8') + "\n")
    except Exception as e:
        print("Error: %s" % str(e))

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
    def __init__(self, id = 0, initialized = False, name = "", overall_rank = None, min_players = None, max_players = None, min_playing_time = None, max_playing_time = None):
        self.id = id
        self.initialized = initialized
        self.name = name
        self.overall_rank = overall_rank
        self.expansion = None
        self.expands = None
        self.yearpublished = 1900
        self.minage = 0
        self.minplayers = min_players
        self.maxplayers = max_players
        self.minplaytime = min_playing_time
        self.maxplaytime = max_playing_time
        self.families = None
        self.mechanics = None
        self.designers = None
        self.artists = None
        self.categories = None

    def set(self, values):
        for k, v in values.items():
            if k in self.__dict__.keys():
                setattr(self, k, v)
        return self

    def set_bgg_game(self, bgg_game):
        self.set(bgg_game._data)
        for rank in bgg_game.ranks:
            if rank.id == 1:
                self.overall_rank = rank.value
        self.initialized = True
        return self

    def is_valid(self):
        return (self.id != 0 and self.name != "") and self.initialized == True

    def print(self):
        print(" == Details: [{}] {} ==".format(self.id, self.name))
        for key, value in self.__dict__.items():
            if key is not "id" and key is not "name" and value is not None:
                print(" {} : {}".format(key, value))

class GameFeatures(object):
    def __init__(self, game, collection):
        assert game.initialized
        self.game = game
        if collection:
            self.collection_owned, self.collection_rating, self.collection_numplays = collection.includes(game.id)
        else:
            self.collection_owned = False
            self.collection_rating = None
            self.collection_numplays = None

        self.player_solo = game.minplayers <= 1 and game.maxplayers >= 1
        self.player_2 = game.minplayers <= 2 and game.maxplayers >= 2
        self.player_3 = game.minplayers <= 3 and game.maxplayers >= 3
        self.player_4 = game.minplayers <= 4 and game.maxplayers >= 4
        self.player_5 = game.minplayers <= 5 and game.maxplayers >= 5
        self.player_X = game.maxplayers > 5

        for mechanic in game.mechanics:
            setattr(self, 'mechanic_' + re.sub(r'\W+', '', mechanic.lower()), True)
        for family in game.families:
            setattr(self, 'family_' + re.sub(r'\W+', '', family.lower()), True)
        for cat in game.categories:
            setattr(self, 'category_' + re.sub(r'\W+', '', cat.lower()), True)
        for artist in game.artists:
            setattr(self, 'artist_' + re.sub(r'\W+', '', artist.lower()), True)
        for designer in game.designers:
            setattr(self, 'artist_' + re.sub(r'\W+', '', designer.lower()), True)

    def is_valid(self):
        return self.initialized

class GameCollection(object):
    def __init__(self, username):
        self.username = username
        self.cache_filename = "data/%s_owned_collection.cache" % self.username
        self.collection_scores = None
        self.bgg = BGGClient()

    def load(self, repository, force_reload = False):
        if not self.username:
            raise Exception("ERROR: no username was defined, please use --user=USERNAME to provide reference.")

        self.collection_scores = []
        try:
            load_cache(self.cache_filename, self.collection_scores)
        except:
            print("Cached file not found. ({})".format(self.cache_filename))

        if len(self.collection_scores) == 0 or force_reload:
            collection  = self.bgg.collection(self.username, own=True)
            if collection:
                for game in collection.items:
                    try:
                        rating = None if not hasattr(game, 'rating') else game.rating
                        numplays = None if not hasattr(game, 'numplays') else game.numplays
                        self.collection_scores.append({'game_id': game.id,'rating': rating, 'numplays': numplays})
                    except Exception as e:
                        print("Error: %s" % str(e))

        # make sure all games from collection are added to central repository
        repository.get_by_ids([item['game_id'] for item in self.collection_scores])

        dump_cache(self.cache_filename, self.collection_scores)
        print("Collection [owned:{}] loaded: {} games".format(self.username, len(self.collection_scores)))

    def includes(self, game_id):
        assert self.collection_scores
        for game in self.collection_scores:
            if game_id == game['game_id']:
                return True, game['rating'], game['numplays']
        return False, None, 0

class GameRepository(object):
    def __init__(self):
        self.games = None
        self.cache_filename = "data/game_repository.cache"
        self.bgg = BGGClient()

    def load(self, force_reload=False, max_pages=20):
        self.games = []
        try:
            load_cache(self.cache_filename, self.games, obj_type=Game)
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
            dump_cache(self.cache_filename, self.games)

        self.validate()
        print("Repository loaded: %d games." % len(self.games))

    def validate(self, retries = 3):
        for run in range(retries):
            invalid_entries = list(filter(lambda x : not x.is_valid(), self.games))
            if len(invalid_entries) == 0:
                return
            print("Loading missing game details from BGG [count: {}].".format(len(invalid_entries)))
            for chunk in tqdm(iterable=list(chunks(invalid_entries, 50)), desc="Loading game details (try:{})".format(run+1), ncols=100):
                games = [game.id for game in chunk]
                for res in self.bgg.game_list(games):
                    self.get_by_id(res.id).set_bgg_game(res)
            dump_cache(self.cache_filename, self.games)

    def get_by_ids(self, id_list, load_missing = True):
        if load_missing:
            game_index = [x.id for x in self.games]
            for missing_id in list(filter(lambda x: x not in game_index, id_list)):
                self.games.append(Game(id=missing_id))
            self.validate()
        return list(filter(lambda x: x.id in id_list and x.is_valid, self.games))

    def get_by_id(self, id, load_missing = True):
        for game in self.games:
            if game.id == id:
                return game

        result = None
        if load_missing:
            bgg_game = self.bgg.game(game_id=id)
            if bgg_game:
                print("Missing ID={}, loading...".format(id))
                result = Game().set_bgg_game(bgg_game)
                self.games.append(result)
        return result

    def get_features(self, collection=None):
        features = {}
        valid_entries = list(filter(lambda x: x.is_valid(), self.games))
        for entry in valid_entries:
            features[entry.id] = GameFeatures(entry, collection)
        feature_dim = set()
        for id, game_features in features.items():
            feature_dim = feature_dim.union(game_features.__dict__.keys())

        print("Features extracted: %d properties identified." % len(feature_dim))

        return features, sorted(feature_dim)