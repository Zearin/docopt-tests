# -*- coding: utf-8 -*-

#
#   Standard Library
#
import io
import json
import linecache
import os


#
#   Extras
#
from lib.decode import (decode_list, decode_dict)


#-------------------------------------------------------------------------------
#   FILES
#-------------------------------------------------------------------------------
def get_fileset_in_dir(path, suffix):
    FILESET = set()
    for filename in os.listdir(path):
        if filename.endswith(suffix):
            FILESET.add(filename)
    return FILESET

CSON_FILES = get_fileset_in_dir('src', '.cson')
JSON_FILES = get_fileset_in_dir('./', '.json'); JSON_FILES.discard('package.json')
BASENAMES  = set([os.path.splitext(f)[0] for f in CSON_FILES])


#-------------------------------------------------------------------------------
#   DATA
#-------------------------------------------------------------------------------
JSON_DATA = dict()

for file in JSON_FILES:
    file = os.path.join('', file)
    with io.open(file, encoding='UTF-8') as f:
        data = json.loads(f.read(), object_hook=decode_dict)
        JSON_DATA.update(data)

FEATURES, SCENARIOS = JSON_DATA.keys(), set()

for item in JSON_DATA.values():
    keys = set(item.keys())
    keys.discard('__desc')
    SCENARIOS.update(keys)


#-------------------------------------------------------------------------------
#   LINE NUMBERS
#-------------------------------------------------------------------------------
for s in SCENARIOS:
    


#-------------------------------------------------------------------------------
#   SANITY CHECK(s)
#-------------------------------------------------------------------------------
for s in SCENARIOS:
    print s
else:
    import sys
    sys.exit(0)