# -*- coding: utf-8 -*-

import re

from decode import *

RE_FLAGS = re.IGNORECASE | re.UNICODE | re.VERBOSE  # | re.DOTALL 
JSON_KEY = re.compile(r'''
    ^(\s+)               # indent
    "                    # dquote
    (   [^"]             # not dquote
        |(?<=\\)"        # OR, a backslash-escaped dquote
    )+                   # 
    "                    # dquote
    :\                   # colon, space
    [{"\[]              # an opening brace, dquote, or bracket
    ''', flags=RE_FLAGS)


def index_keys(lines):
    '''Build a list of (index, string) matches of JSON keys.'''
    
    matches = []
    for idx, line in enumerate(lines, start=1):
        is_match = JSON_KEY.match(line)
        if is_match:
            matches.append( (idx, is_match.string) )
    return matches
