# -*- coding: utf-8 -*-
'''Helper for the ``json`` module. Can be used with the ``object_hook`` arguments to 
force the Python representation of JSON to use `str` objects instead of `unicode`.

Adapted from:
    http://stackoverflow.com/a/6633651/180290

'''

from collections import OrderedDict
import json

def decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = decode_list(item)
        elif isinstance(item, dict):
            item = decode_dict(item)
        rv.append(item)
    return rv

def decode_dict(data, ordered_dict=False):
    if ordered_dict:
        rv = OrderedDict()
    else:
        rv = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = decode_list(value)
        elif isinstance(value, dict):
            value = decode_dict(value)
        rv[key] = value
    return rv

def decode_ordered_dict(data):
    return decode_dict(data, ordered_dict=True)


class DocOptJSONDecoder(json.JSONDecoder):
    '''Slightly-tweaked subclass of the normal JSONDecoder.
    '''
    
    def __init__(self, *args, **kw):
        
        # Standardize `object_hook`, `encoding`, and `strict` args
        kw.update({
            'object_hook':       kw.get('object_hook',       decode_dict),
            'object_pairs_hook': kw.get('object_pairs_hook', OrderedDict),
            'encoding':          kw.get('encoding',          'UTF-8'),
            'strict':            kw.get('strict',            False)
        })
        
        super(DocOptJSONDecoder, self).__init__(*args, **kw)
