docopt-tests
============

- **CSON** for human-friendly tests.
- **JSON** for ultimate test portability.
- **Docopt tests for all.**

Everything here is minimal.  If this project gains traction, I’ll spruce things up. :-) 


## Motivation

See [docopt issue #105](https://github.com/docopt/docopt/issues/105).


## Using the JSON tests

Pseudocode:

```
data = read_json_file()         # 1. grab the test data

forEach key in data:
    docstring = key             # 2. top-level keys are docstrings
    tests = data[key]           # 3. each contains an Array of tests
    
    forEach test in tests:      # 4. run the tests
        argv = test['input']
        expected = test['expected']
        assert docopt(docstring, argv, help=False) == expected

                                # And you're done!
```
