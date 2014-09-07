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

def get_line_indeces(lines, indent='  '):
    '''Return a dict whose keys are categories of indeces, and whose values are lists containing 
    (line_number, string) tuples.
    '''
    
    key_indeces      = index_keys(lines)
    result = {
        'keys':         key_indeces,
        'features':     [i for i in key_indeces if i[1].startswith(1*indent + '"')  ],
        'scenarios':    [i for i in key_indeces if i[1].startswith(2*indent + '"') and 
                                                    '__desc' not in i[1]            ],
        'usages':       [i for i in key_indeces if i[1].startswith(3*indent + '"')  ],
        'tests':        [i for i in key_indeces if i[1].startswith(5*indent + '"input":') ]
    }
    return result
    
    