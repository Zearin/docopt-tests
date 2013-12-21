import  atexit
from    collections import defaultdict, namedtuple
import  json


from docopt import (docopt, DocoptExit, DocoptLanguageError)
from pyvows import (Vows, expect)


#--------------------------------------------------------------------------------

JSON_DATA = None

with open('test.json') as f:
    JSON_DATA = json.loads( f.read() )

JSON_DATA = JSON_DATA['test-batches']   # Ignore the outermost container
FAILED_USAGES = []                      # store tuples (doc, argv, expected) of failed tests

def show_failed_usages():
    from pprint import pprint
    import colorama 
    from colorama import (Fore, Back, Style)
     
    usages = frozenset([doc[0] for doc in FAILED_USAGES])
    
    for doc in usages:
        failures = [ i[1:] for i in FAILED_USAGES if i[0] == doc  ]
        print
        print "{0.WHITE}{1}{0.RESET}".format( Fore, doc )
        for f in failures:
            print "\t{0}".format(f[0])
    
    print "\nTotal Failures: {0}".format(len(FAILED_USAGES))
    
atexit.register(show_failed_usages)

#--------------------------------------------------------------------------------

@Vows.batch
class DocoptJSON(Vows.Context):
    
    def topic(self):
        # for idx, item in enumerate(JSON_DATA):
        #     yield idx, item
        for item in JSON_DATA:
            yield item
    
    def should_be_a_dict(self, topic):
        expect(topic).to_be_instance_of(dict)
    
    
    class JsonTests(Vows.Context):
            
        def topic(self, topic):
            topic['doc'] = str(topic['doc']) # docopt hates unicode
            for test in topic['tests']:
                yield {
                    'doc':      topic['doc'], 
                    'argv':     test['input'], 
                    'expected': test['expected']
                }
        
        def doc_is_a_string(self, topic):
            expect(topic['doc']).to_be_instance_of(str)

        def argv_is_unicode(self, topic):
            expect(topic['argv']).to_be_instance_of(unicode)
        
        def error_tests_raise_errors(self, topic):
            doc, argv, expected = topic['doc'], topic['argv'], topic['expected']
            
            if expected == u'user-error':
                try:
                    expect(docopt(doc, argv, help=False)).to_be_an_error()
                except (DocoptExit,SystemExit): # prevent docopt from stopping testing
                    pass
                except AssertionError as err:
                    FAILED_USAGES.append( (doc, str(argv), str(expected)) )
                    raise err

        def parsing_tests_pass(self, topic):
            doc, argv, expected = topic['doc'], topic['argv'], topic['expected']
            
            if expected != u'user-error':
                try:
                    expect(docopt(doc, argv, help=False)).to_equal(expected)
                except (DocoptExit,SystemExit): # prevent docopt from stopping testing
                    pass
                except AssertionError as err:
                    FAILED_USAGES.append( (doc, str(argv), str(expected)) )
                    raise err
