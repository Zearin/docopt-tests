# -*- coding: utf-8 -*-

import envoy

def lookup_srcmap(file, line, cwd):
    '''Given ``file`` and ``line``, runs the command ``source-map-peek`` to lookup the 
    equivalent location in the *.cson file.
    '''
    args   = '../node_modules/.bin/source-map-peek --padding 4 {0}:{1}'.format(file, line)
    kw     = dict(cwd=cwd)
    result = envoy.run(args, **kw)
    
    if result.status_code is 0:
        return result
    else:
        import sys
        sys.exit('ERROR LOOKING UP SOURCE MAP FOR: ' + file)