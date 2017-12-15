#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from bggdata import GameRepository, GameCollection

VERBOSE = False
ACTIONS = None
FORCE_RELOAD = False
USERNAME = None

def printSysInformation():
    import boardgamegeek2
    print('BGGLib: {}'.format(boardgamegeek2.__version__))

def getCmdArgs(argv):
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

    getCmdArgs(sys.argv)
    printSysInformation()

    # load top 2000 games
    repository = GameRepository()
    repository.load(FORCE_RELOAD, max_pages=1)
    repository.getById(28143).print()

    # # load user collection
    # collection = GameCollection(USERNAME)
    # collection.load(FORCE_RELOAD)
