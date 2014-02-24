# -*- coding: utf-8 -*-

import  atexit
import  io
import  os
import  json

from docopt import (docopt, DocoptExit, DocoptLanguageError)
from pyvows import (Vows, expect)

#--------------------------------------------------------------------------------

FAILED_USAGES = dict()

def _update_failed_usage(topic):
    doc, failure = topic['doc'], topic['argv']
    if doc not in FAILED_USAGES:
        FAILED_USAGES[doc] = [] #set()
    FAILED_USAGES[doc].append(failure)

def _show_failed_usages():
    from pprint import pprint
    from colorama import (Fore, Back, Style)
    
    for doc, fails in FAILED_USAGES.items():
        print 
        print "{Fore.WHITE}{doc}{Fore.RESET}".format(Fore=Fore, doc=doc)
        for fail in fails:
            print "    {0}".format(fail)
        print
        
    print "\n{Fore.WHITE}Total Failures: {0}{Fore.RESET}".format(len(FAILED_USAGES), Fore=Fore)
    
atexit.register(_show_failed_usages)

#-------------------------------------------------------------------------------

JSON_DATA = None
with io.open('all_tests.json', encoding='UTF-8') as f:
    JSON_DATA = json.loads(f.read(), object_hook=_decode_dict)

FEATURES  = JSON_DATA.keys()
SCENARIOS = set()

for item in JSON_DATA.values():
    keys = set(item.keys())
    keys.discard('__desc')
    SCENARIOS.update(keys)

for s in SCENARIOS:
    print s
else:
    import sys
    sys.exit(0)


#-------------------------------------------------------------------------------

### TODO: Write code to:
###
###     - fetch the CSON
###     - scan it for feature/scenario/usage/input test lines
###     - report which failed

#-------------------------------------------------------------------------------


@Vows.batch
class DocoptVows(Vows.Context):
    def topic(self):
        for feature_name, feature_obj in JSON_DATA.items():
            if '__desc' in feature_obj:
                del feature_obj['__desc'] # not used in tests
            yield feature_name, feature_obj
    
    
    class FeatureContext(Vows.Context):
        def contents_are_a_dict(self, topic):
            expect(topic[1]).to_be_instance_of(dict)


        class ScenarioContext(Vows.Context):
            def topic(self, topic):
                scenario = topic[1]
                for name, scenario_obj in scenario.items():
                    yield name, scenario_obj
            
            def we_have_parsed_the_JSON_correctly(self, topic):
                name, scenario_obj = topic
                expect(name).to_be_instance_of(str)
                expect(scenario_obj).to_be_instance_of(dict)

            
            class Usage(Vows.Context):
                def topic(self, topic):
                    name, scenario_obj = topic
                    for usage, tests in scenario_obj.items():
                        for test in tests:
                            yield {
                                'doc':      usage, 
                                'argv':     test['input'],
                                'expected': test['expected']
                            }
            
                def error_tests_raise_errors(self, topic):
                    doc, argv, expected = topic['doc'], topic['argv'], topic['expected']
                    if expected == 'user-error':
                        try:
                            expect(docopt(doc, argv, help=False)).to_be_an_error()
                        except (DocoptExit,SystemExit): # else docopt stops the testing
                            pass
                        except AssertionError as err:
                            _update_failed_usage(topic)
                            raise err
                
                def parsing_tests_pass(self, topic):
                    doc, argv, expected = topic['doc'], topic['argv'], topic['expected']
                    if expected != 'user-error':
                        try:
                            expect(docopt(doc, argv, help=False)).to_equal(expected)
                        except (DocoptExit,SystemExit): # prevent docopt from stopping testing
                            pass
                        except AssertionError as err:
                            _update_failed_usage(topic)
                            raise err
