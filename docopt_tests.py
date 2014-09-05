# -*- coding: utf-8 -*-

# Standard Lib
from    __future__  import (print_function, with_statement, unicode_literals)
import  atexit
import  json
import  logging
import  re

# Helpers
import  lib, lib.json
from path   import path

# Testing
from preggy import expect

# Test subjects
from docopt import (docopt, DocoptExit)

#--------------------------------------------------------------------------------

FAILURES    = {}

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
    result     = [match.group(1), int(match.group(2))]
    return result

#-------------------------------------------------------------------------------

import contextlib

@contextlib.contextmanager
def scenario_context(ctx):
    #error_in_scenario = False
    log.info('SCENARIO: %s', scenario_name)
    
    ctx['scenario_line'] = None
    for line, value in indeces['scenarios']:
        if ctx['scenario_name'] in value:
            ctx['scenario_line'] = line
    
    yield ctx
    
    for i in ('scenario_name','scenario','scenario_line'):
        del ctx[i]
        


@contextlib.contextmanager
def usage_context(ctx):
    #error_in_usage = False
    log.info('%s', usage)
    
    ctx['usage_line'] = None
    for line, value in indeces['usages']:
        if line < ctx['scenario_line']:  # Skip earlier lines
            continue
        if usage in value.replace(r'\n', '\n'):  #  Usages often span multiple lines
            ctx['usage_line'] = line
    
    try:
        ctx['next_usage_line'] = min([line for line, value in indeces['usages'] if line > ctx['usage_line']])
    except ValueError:
        ctx['next_usage_line'] = 0
    
    yield ctx
    
    for i in ('usage_index','usage','tests','usage_line','next_usage_line'):
        del ctx[i]

@contextlib.contextmanager
def test_context(ctx):
    # TESTS
    ctx['test_line'] = None
    for line, value in [(line, value) for (line, value) in indeces['tests']
                        if (ctx['next_usage_line'] > line > ctx['usage_line']) ]:
        if test['input'] in value:
            ctx['test_line'] = line
    
    log.info('ARGV: %s', test['input'])
    
    # run the test
    try:
        argv, expected = test['input'], test['expected']
        if expected == 'user-error':
            try:
                expect( docopt(ctx['usage'], argv, help=False) ).to_be_an_error()
            except (DocoptExit,SystemExit): # prevent docopt from stopping testing
                pass
        else:
            try:
                expect( docopt(ctx['usage'], argv, help=False) ).to_equal(expected)
            except (DocoptExit,SystemExit): # prevent docopt from stopping testing
                pass
    
    # test failed
    except AssertionError as err:
        _error_source = lib.src_map_peek(
            ctx['file_obj'].basename(), 
            ctx['test_line'],
            cwd=BUILDDIR)
        _error_ctx = _scrape_srcmap_stdout(_error_source.std_out)
        if _error_ctx[0].startswith('../src'):
            _error_ctx[0] = _error_ctx[0][3:]
        ctx['error'] = _error_ctx
        
    finally:
        yield ctx
        #_handle_failed_test(fail_data)
        for i in ('test_index','test','test_line','error'):
            try:                del ctx[i]
            except KeyError:    pass


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
    
    ctx = {
        'file_obj': testfile,
        'indeces':  indeces
    }
    
    
    # FEATURES
    for feature_name, feature in json_data.items():
        #error_in_feature = False
        log.info('FEATURE: %s', feature_name)
        
        ctx.update({
            'feature_name': feature_name,
            'feature':      feature
        })
        
        
        # SCENARIOS
        for scenario_name, scenario in ctx['feature'].items():
            if scenario_name == '__desc':  # skip descriptions
                continue
            
            ctx.update({
                'scenario_name': scenario_name,
                'scenario':      scenario 
            })
            
            
            with scenario_context(ctx) as ctx:
                
                
                # USAGE
                for usage_index, (usage, tests) in enumerate(ctx['scenario'].items()):
                    ctx.update({
                        'usage_index': usage_index,
                        'usage':       usage,
                        'tests':       tests
                    })
                    
                    
                    with usage_context(ctx) as ctx:
                        for test_index, test in enumerate(ctx['tests']):
                            ctx.update({
                                'test_index': test_index,
                                'test':       test
                            })
                            
                            with test_context(ctx) as ctx:
                                if 'error' in ctx:
                                    src_file, src_line = ctx['error']
                                    
                                    if src_file not in FAILURES:
                                        FAILURES[src_file] = []
                                    FAILURES[src_file].append(src_line)
                            
        
    
for src_file, line_numbers in FAILURES.iteritems():
    print(src_file)
    for i in sorted(line_numbers):
        print('\t{0}'.format(i))


# # Report the test results
# if len(FAILURES) == 0:
#     log.info('No tests were failed!')
# else:
#     log.warn('{0} failed tests'.format(len(FAILURES)))
