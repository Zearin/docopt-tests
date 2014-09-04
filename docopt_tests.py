# -*- coding: utf-8 -*-

# Standard Lib
from    __future__  import (print_function, with_statement, unicode_literals)
import  atexit
import  collections
import  io
import  json
import  logging
import  os
import  re
import  subprocess

# Helpers
import  lib, lib.json
from    path   import path
import  envoy

# Testing
from preggy import expect

# Test subjects
from docopt import (docopt, DocoptExit, DocoptLanguageError)

#--------------------------------------------------------------------------------

FAILURES = []

SRCDIR      = 'src'
BUILDDIR    = 'build'
INDENT      = '  '
TESTFILES   = path(BUILDDIR).files('*.json')

log = logging.getLogger('docopt_tests')
log.setLevel(logging.WARN)

#--------------------------------------------------------------------------------
    
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
    
    
    lookup_result = lib.lookup_srcmap(path(file).basename(), kw['usage_data'][0], BUILDDIR)
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

def _scrape_srcmap_stdout(srcmap_out):
    '''Scrapes the the output of :func:`lookup_srcmap`, and returns a tuple ``(file, line)``.
    '''
    
    FLAGS     = re.IGNORECASE|re.MULTILINE|re.IGNORECASE|re.UNICODE#|re.DEBUG
    SRCMAP_RE = re.compile(
        r'''^file:\s(.+)\nline:\s(\d+)\s''',
        flags=FLAGS)
    
    # relevant data is in the last 2 lines of output
    srcmap_out = '\n'.join( srcmap_out.splitlines()[-2:] )
    match      = SRCMAP_RE.match(srcmap_out)
    result     = match.group(0), match.group(1)
    return result

#-------------------------------------------------------------------------------

def process_json(json_obj, indeces):
    # FEATURES
    for feature_name, feature in json_data.items():
        #error_in_feature = False
        log.info('FEATURE: %s', feature_name)
        
        # SCENARIOS
        for scenario_name, scenario in feature.items():
            if scenario_name == '__desc':  # skip descriptions
                continue
            
            #error_in_scenario = False
            log.info('SCENARIO: %s', scenario_name)
            
            scenario_line = None
            for line, value in indeces['scenarios']:
                if scenario_name in value:
                    scenario_line = line
            
            # USAGE
            for usage_index, (usage, tests) in enumerate(scenario.items()):
                #error_in_usage = False
                log.info('%s', usage)
                
                usage_line = None
                for line, value in indeces['usages']:
                    if line < scenario_line:  # Skip earlier lines
                        continue
                    if usage in value.replace(r'\n', '\n'):  #  Usages often span multiple lines
                        usage_line = line
                
                try:
                    next_usage_line = min([line for line, value in indeces['usages'] if line > usage_line])
                except ValueError:
                    next_usage_line = 0
                
                # TESTS
                for test_index, test in enumerate(tests):
                    argv, expected = test['input'], test['expected']
                    
                    test_line = None
                    for line, value in [(line, value) for (line, value) in indeces['tests']
                                        if (next_usage_line > line > usage_line) ]:
                        if argv in value:
                            test_line = line
                    
                    log.info('ARGV: %s', argv)
                    
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
                            'test_line':    test_line,
                            'test':         test,
                            'error':        err
                        }
                        
                        result = lib.lookup_srcmap(
                            fail_data['file'], 
                            test_line,
                            cwd=BUILDDIR)

                        src_file, src_line = _scrape_srcmap_stdout(result.std_out)
                        FAILURES.append(fail_data)
                        
                        #_handle_failed_test(fail_data)
    
    log.debug('%s: DONE\n', testfile.relpath())

#-------------------------------------------------------------------------------
# JSON File
for testfile in TESTFILES:
    
    log.debug('='*80)
    log.debug('%s', testfile.relpath())
    log.debug('='*80)
    
    # First, index the important keys
    #
    # (necessary because there's no way to tell the result of `json.loads()`:
    #  "give me the line number for this key")
    #
    lines     = testfile.lines(encoding='UTF-8')
    indeces   = lib.json.get_line_indeces(lines, indent=INDENT)
    
    log.debug('\t%d Features',  len(indeces['features']))
    log.debug('\t%d Scenarios', len(indeces['scenarios']))
    log.debug('\t%d Usages',    len(indeces['usages']))
    
    # Deserialize JSON
    contents  = testfile.text(encoding='UTF-8')
    json_data = json.loads(
        contents, 
        object_hook=lib.json.decode.decode_dict, 
        encoding   ='UTF-8', 
        strict     =False
        )
    
    process_json(json_data, indeces)
    


# Report the test results
if len(FAILURES) == 0:
    log.info('No tests were failed!')
else:
    log.warn('{0} failed tests'.format(len(FAILURES)))
