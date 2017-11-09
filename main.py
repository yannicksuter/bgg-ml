#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from bggdata import GameCollection

FORCE_RELOAD = False
USERNAME = None

def getCmdArgs(argv):
    for arg in sys.argv:
        try:
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
        print("usage: %s --force_online --user=USERNAME" % sys.argv[0].split('/')[-1])
        sys.exit(0)

    getCmdArgs(sys.argv)

    collection = GameCollection(USERNAME)
    collection.load(FORCE_RELOAD)

    # collection.show()