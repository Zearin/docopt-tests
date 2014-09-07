# -*- coding: utf-8 -*-

# Standard Lib
from    __future__  import (print_function, with_statement, unicode_literals)
import  atexit
import  contextlib
import  json
import  logging
import  re
import  textwrap

# Helpers
from    colorama import (Fore, Style)
import  lib, lib.json
from    path   import path

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

log         = None

#--------------------------------------------------------------------------------

def _handle_failed_test( ctx ):
    src_file, src_line = ctx['cson_err_location']
    src_map_peek = ctx['src_map_peek']
    feature, scenario, usage = ctx['feature_name'], ctx['scenario_name'], ctx['usage']

    if src_file not in FAILURES:
        FAILURES[src_file] = set()
    if src_line not in FAILURES[src_file]:
        FAILURES[src_file].add((src_map_peek, ctx['error']))

    # if feature not in FAILURES[src_file]:
    #     FAILURES[src_file][feature] = {}
    # if scenario not in FAILURES[src_file]:
    #     FAILURES[src_file][scenario] = {}
    # if usage not in FAILURES[src_file][scenario]:
    #     FAILURES[src_file][scenario][usage] = set()
    #
    # FAILURES[src_file][scenario][usage].add(src_line)

def _show_failed_usages():
    from pprint import pprint
    from colorama import (Fore, Back, Style)

    FAILCOUNT=0

    for scenario in FAILURES.keys():
        print('{Style.DIM}{banner}{Style.RESET_ALL}'.format(Style=Style, banner=('-' * 80)))
        print(scenario)
        print()

        for doc, failures in FAILURES[scenario].items():
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

@contextlib.contextmanager
def feature_context(ctx, **f_ctx):
    log.info('FEATURE: %s', f_ctx['feature_name'])
    
    ctx.update(f_ctx)
    
    yield ctx
    
    for key in f_ctx.keys():
        del ctx[key]

@contextlib.contextmanager
def scenario_context(ctx, **s_ctx):
    log.info('SCENARIO: %s', s_ctx['scenario_name'])

    s_ctx['scenario_line'] = None
    for line, value in ctx['indeces']['scenarios']:
        if s_ctx['scenario_name'] in value:
            s_ctx['scenario_line'] = line

    ctx.update(s_ctx)

    yield ctx

    for key in s_ctx.keys():
        del ctx[key]


@contextlib.contextmanager
def usage_context(ctx, **u_ctx):
    log.info('%s', u_ctx['usage'])

    u_ctx['usage_line'] = None
    for line, value in ctx['indeces']['usages']:
        if line < ctx['scenario_line']:  # Skip earlier lines
            continue
        if u_ctx['usage'] in value.replace(r'\n', '\n'):  #  Usages often span multiple lines
            u_ctx['usage_line'] = line

    try:
        u_ctx['next_usage_line'] = min([line for line, value in ctx['indeces']['usages'] if line > u_ctx['usage_line']])
    except ValueError:
        u_ctx['next_usage_line'] = 0

    ctx.update(u_ctx)

    yield ctx

    for key in u_ctx:
        del ctx[key]

@contextlib.contextmanager
def test_context(ctx, **t_ctx):
    # TESTS
    t_ctx['test_line'] = None

    for line, value in [
        (line, value) for (line, value) in ctx['indeces']['tests']
        if ctx['next_usage_line'] > line > ctx['usage_line']
    ]:
        if t_ctx['test']['input'] in value:
            t_ctx['test_line'] = line

    log.info('ARGV: %s', t_ctx['test']['input'])

    # run the test
    try:
        argv, expected = t_ctx['test']['input'], t_ctx['test']['expected']
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
        ctx['error'] = err
        
        _src_map_peek = lib.src_map_peek(
            ctx['testfile'].basename(),
            t_ctx['test_line'],
            cwd=BUILDDIR)
         
        # fix results (they're relative to BUILDDIR)
        _src_map_peek.std_out =  _src_map_peek.std_out.replace('../src', 'src')
        
        ctx['src_map_peek'] = _src_map_peek.std_out
        ctx['cson_err_location'] = _scrape_srcmap_stdout(_src_map_peek.std_out)
        
        

    finally:
        yield ctx

        for key in t_ctx.keys():
            try:
                del ctx[key]
            except KeyError:
                pass


# JSON File
for testfile in TESTFILES:
    
    # Grab a file-specific logger 
    log = logging.getLogger(testfile.namebase)
    log.setLevel(logging.WARN)
    
    handler = logging.StreamHandler()
    handler.setLevel(logging.WARN)
    
    formatter = logging.Formatter('%(name)s:%(message)s')
    
    handler.setFormatter(formatter)
    log.addHandler(handler)
    
    # Begin
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
        'testfile': testfile,
        'indeces':  indeces
    }


    # FEATURES
    for feature_name, feature in json_data.items():
        
        with feature_context(ctx, feature_name=feature_name, feature=feature) as ctx:
            
            # SCENARIOS
            for scenario_name, scenario in ctx['feature'].items():
                if scenario_name == '__desc':  # skip descriptions
                    continue

                with scenario_context(ctx, scenario_name=scenario_name, scenario=scenario) as ctx:

                    # USAGES
                    for usage_index, (usage, tests) in enumerate(ctx['scenario'].items()):

                        with usage_context(ctx, usage_index=usage_index, usage=usage, tests=tests) as ctx:
                            
                            # TESTS
                            for test_index, test in enumerate(ctx['tests']):

                                with test_context(ctx, test_index=test_index, test=test) as ctx:
                                    if 'error' in ctx:
                                        _handle_failed_test(ctx)


#  Report results when testing is complete
if len(FAILURES):
    FAILCOUNT = 0
    
    preggywrap = textwrap.TextWrapper(
        break_long_words    = False,
        break_on_hyphens    = False,
        initial_indent      = INDENT*2,
        subsequent_indent   = INDENT*2,
        drop_whitespace     = False,
        replace_whitespace  = False,
        expand_tabs         = False,
        width               = 120
        )
    
    srcmapwrap = textwrap.TextWrapper(
        break_long_words    = False,
        break_on_hyphens    = False,
        initial_indent      = INDENT*4,
        subsequent_indent   = INDENT*4,
        drop_whitespace     = False,
        replace_whitespace  = False,
        expand_tabs         = False,
        width               = 100
        )
    
    for key in FAILURES.keys():
        print(Style.BRIGHT, key, Style.RESET_ALL)
        
        for failure in FAILURES[key]:
            FAILCOUNT += 1
            src_map_peek, err = failure
            
            print('\n\n', Fore.YELLOW, preggywrap.fill(str(err)), Fore.RESET, sep=None, end='\n\n')
            for line in src_map_peek.splitlines():
                print(''.join(srcmapwrap.wrap(line)))
        
        print('\n')
        

    print('TOTAL FAILURES: %s' % FAILCOUNT)
