import  atexit
import  io
import  json

from docopt import (docopt, DocoptExit, DocoptLanguageError)
from pyvows import (Vows, expect)

#--------------------------------------------------------------------------------

FAILED_USAGES = dict()

# http://stackoverflow.com/a/6633651/180290
def _decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv

def _decode_dict(data):
    rv = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = _decode_list(value)
        elif isinstance(value, dict):
            value = _decode_dict(value)
        rv[key] = value
    return rv


def update_failed_usage(topic):
    doc, failure = topic['doc'], topic['argv']
    if doc not in FAILED_USAGES:
        FAILED_USAGES[doc] = [] #set()
    FAILED_USAGES[doc].append(failure)

def show_failed_usages():
    from pprint import pprint
    from colorama import (Fore, Back, Style)
    
    for doc, fails in FAILED_USAGES.items():
        print 
        print "{Fore.WHITE}{doc}{Fore.RESET}".format(Fore=Fore, doc=doc)
        for fail in fails:
            print "    {0}".format(fail)
        print
        
    print "\n{Fore.WHITE}Total Failures: {0}{Fore.RESET}".format(len(FAILED_USAGES), Fore=Fore)
    
atexit.register(show_failed_usages)

#--------------------------------------------------------------------------------

@Vows.batch
class DocoptJSON(Vows.Context):
    def topic(self):
        JSON_DATA = None
        with io.open('all_tests.json', encoding='UTF-8') as f:
            JSON_DATA = json.loads(f.read(), object_hook=_decode_dict)
        for doc, tests in JSON_DATA.items():
            yield doc, tests
    
    
    class JsonTests(Vows.Context):
        def topic(self, topic):
            doc, tests  = topic
            for test in tests:
                yield {
                    'doc':      doc, 
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
                    update_failed_usage(topic)
                    raise err

        def parsing_tests_pass(self, topic):
            doc, argv, expected = topic['doc'], topic['argv'], topic['expected']
            if expected != 'user-error':
                try:
                    expect(docopt(doc, argv, help=False)).to_equal(expected)
                except (DocoptExit,SystemExit): # prevent docopt from stopping testing
                    pass
                except AssertionError as err:
                    update_failed_usage(topic)
                    raise err
