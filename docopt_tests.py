# -*- coding: utf-8 -*-

# Standard Lib
from    __future__  import (print_function, with_statement)
import  atexit
import  collections
import  io
import  json
import  os
import  re
import  subprocess


# Helpers
from lib    import decode
from path   import path
import envoy

# Testing
from preggy import expect

# Test subjects
from docopt import (docopt, DocoptExit, DocoptLanguageError)

#--------------------------------------------------------------------------------

FAILURES = dict()

SRCDIR   = 'src'
BUILDDIR = 'build'
INDENT   = '  '

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





def _lookup_srcmap(file, line):
    args = '../node_modules/.bin/source-map-peek {1}:{2}'.format(BUILDDIR, file, line),
    kw   = dict(cwd=BUILDDIR)
    
    result = envoy.run(*args, **kw)
    return result
    
def _handle_failed_test( kw ):
    file, scenario, usage = kw['file'], kw['scenario_data'][1], kw['usage_data'][1]
    
    if file not in FAILURES:
        FAILURES[file] = {}
    # if feature not in FAILURES[file]:
    #     FAILURES[file][feature] = {}
    if scenario not in FAILURES[file]:
        FAILURES[file][scenario] = {}
    if usage not in FAILURES[file][scenario]:
        FAILURES[file][scenario][usage] = []
    
    FAILURES[file][scenario][usage].append(kw)
    
    
    lookup_result = _lookup_srcmap(path(file).basename(), kw['usage_data'][0])
    lookup_output = lookup_result.std_out.splitlines()
    print(lookup_output[-2:])
    
    print('Failed test #{test_index} for usage:{usage_data[1]}'.format( **kw ) )
    
    
    

def _show_failed_usages():
    from pprint import pprint
    from colorama import (Fore, Back, Style)
    
    for idx, i in enumerate(args):
        indent = ' ' * idx
        i = str(i)
        print(indent + i)
    
    FAILCOUNT=0
    
    for scenario in FAILED_USAGES.keys():
        print('{Style.DIM}{banner}{Style.RESET_ALL}'.format(Style=Style, banner=('-' * 80)))
        print(scenario)
        print()
        
        for doc, failures in FAILED_USAGES[scenario].items():
            print("  {Fore.WHITE}{Style.DIM}{banner}{Style.RESET_ALL}{Fore.RESET}".format(Fore=Fore, Style=Style, banner=('-' * 80) ))
            print("  {Fore.WHITE}{doc}{Fore.RESET}".format(Fore=Fore, doc=doc))
            for fail in failures:
                print("    {Fore.RED}{0}{Fore.RESET}".format(fail,Fore=Fore))
                FAILCOUNT += 1
            print()
        
        print()
        print()
        

    print("\n{Fore.WHITE}Total Failures: {0}{Fore.RESET}".format(FAILCOUNT, Fore=Fore))

    
#atexit.register(_show_failed_usages)

#-------------------------------------------------------------------------------

class DocOptJSONDecoder(json.JSONDecoder):
    '''Slightly-tweaked subclass of the normal JSONDecoder.
    '''
    
    def __init__(self, *args, **kw):
        # Standardize `object_hook`, `encoding`, and `strict` args
        kw.update({
            'object_hook': decode.decode_dict,
            'object_pairs_hook': collections.OrderedDict,
            'encoding': 'UTF-8',
            'strict': False
        })
        
        super(DocOptJSONDecoder, self).__init__(*args, **kw)

def index_keys(lines):
    matches = []
    for idx, line in enumerate(lines, start=1):
        is_match = JSON_KEY.match(line)
        if is_match:
            matches.append( (idx, is_match.string) )
    return matches


# JSON File
for testfile in path( BUILDDIR ).files('*.json'):
    
    # First, index the important keys
    #
    # (necessary because there's no way to tell the result of `json.loads()`:
    #  "give me the line number for this key")
    #
    lines     = testfile.lines(encoding='UTF-8')
    
    key_indeces      = index_keys(lines)
    feature_indeces  = [i for i in key_indeces if i[1].startswith(1*INDENT + '"') ]
    scenario_indeces = [i for i in key_indeces if i[1].startswith(2*INDENT + '"')
                                              and '__desc' not in i[1]            ]
    usage_indeces    = [i for i in key_indeces if i[1].startswith(3*INDENT + '"') ]
    
    # Deserialize JSON
    contents  = testfile.text(encoding='UTF-8')
    json_data = json.loads(contents, cls=DocOptJSONDecoder)
    
    
    # FEATURES
    for feature_name, feature in json_data.items():
        error_in_feature = False
        
        # SCENARIOS
        for scenario_name, scenario in feature.items():
            if scenario_name == '__desc':  # skip descriptions
                continue
            error_in_scenario = False
            scenario_line = None
            
            for line, value in scenario_indeces:
                if scenario_name in value:
                    scenario_line = line
            
            
            # USAGE
            for usage, tests in scenario.items():
                error_in_usage = False
                
                usage_line = None
                for line, value in usage_indeces:
                    if usage in value.replace(r'\n', '\n'):
                        usage_line = line
                
                
                # TESTS
                for test_index, test in enumerate(tests):
                    argv, expected = test['input'], test['expected']
                    
                    try:
                        if expected == 'user-error':
                            try:
                                expect( docopt(usage, argv, help=False) ).to_be_an_error()
                            except (DocoptExit,SystemExit): # prevent docopt from stopping testing
                                pass
                        else:
                            try:
                                expect( docopt(usage, argv, help=False) ).to_equal(expected)
                            except (DocoptExit,SystemExit): # prevent docopt from stopping testing
                                pass
                    
                    # test failed
                    except AssertionError as err:
                        fail_data = {
                            'file_obj':     testfile,
                            'file':         testfile.basename(),
                            
                            'scenario_data': (scenario_line, scenario_name),
                            'usage_data':    (usage_line, usage),
                            'test_index':   test_index,
                            'test':         test,
                            'error':        err
                        }

                        _handle_failed_test(fail_data)
                        
                        
