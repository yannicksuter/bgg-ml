#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from bggdata import GameRepository, GameCollection
from bgganalytics import GameAnalytics

VERBOSE = False
ACTIONS = None
FORCE_RELOAD = False
USERNAME = None

def print_sys_information():
    import boardgamegeek2
    print('BGGLib: {}'.format(boardgamegeek2.__version__))
    if FORCE_RELOAD:
        print('Data: Fetch online resources')
    else:
        print('Data: Use cached data if available')

def process_cmd_args(argv):
    for arg in sys.argv:
        try:
            if arg.startswith("--verbose") or arg.startswith("-v"):
                global VERBOSE
                VERBOSE = True
            if arg.startswith("--action="):
                global ACTIONS
                ACTIONS = arg[len("--action="):]
            if arg.startswith("--force_online"):
                global FORCE_RELOAD
                FORCE_RELOAD = True
            elif str(arg).startswith("--user="):
                global USERNAME
                USERNAME = str(arg).split("=")[-1]
        except:
            pass

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("usage: %s --action==[dump_collection,get_details]--force_online --user=USERNAME" % sys.argv[0].split('/')[-1])
        sys.exit(0)

    process_cmd_args(sys.argv)
    # FORCE_RELOAD = True
    print_sys_information()

    # load top 2000 games
    repository = GameRepository()
    repository.load(FORCE_RELOAD, max_pages=1)

    # # load user collection
    collection = GameCollection(USERNAME)
    collection.load(repository, FORCE_RELOAD)

    # print("")
    # repository.getById(71).print()
    # repository.getById(163930).print()

    features = repository.get_features(collection=collection)
    analytics = GameAnalytics(repository)
    analytics.get_clusters(collection)