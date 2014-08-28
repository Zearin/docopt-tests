'''Builds *.cson files into *.json files, and source maps.
'''

#--------------------------------------------------------------------------------

# Standard Library
from __future__ import print_function

# External
from path import path


#--------------------------------------------------------------------------------

SRCDIR   = 'src'
BUILDDIR = 'build'

CMD = 'coffee --bare --no-header --map --output {BUILDDIR} --compile {SRCDIR}/*.cson'
CMD = CMD.format(BUILDDIR=BUILDDIR, SRCDIR=SRCDIR)

#--------------------------------------------------------------------------------


def clean_lines(lines):
    '''Removes JSON-invalid cruft from the lines.'''
    
    lines[0]  = lines[0].replace('('  , '')
    lines[-3] = lines[-3].replace(');', '')
    lines     = lines[:-2]
    return lines


def process_js(file):
    file = path(file)
    
    # Cleanup
    lines = file.lines()
    lines = clean_lines(lines)
    file.write_lines(lines)
    
    # Rename the file
    namebase = file.namebase
    newname = path.joinpath(BUILDDIR, namebase + '.json')
    file.rename(newname)


def process_map(file):
    file = path(file)
    
    # Point map to the new file
    lines = file.lines()
    lines[2] = lines[2].replace('.js"', '.json"')
    file.write_lines(lines)
    
    # Rename the file
    newname = path.joinpath(BUILDDIR, file.basename().replace('.js.map', '.json.map'))
    file.rename(newname)
    
#--------------------------------------------------------------------------------

if __name__ == '__main__':
    import subprocess
    
    subprocess.check_call(CMD, shell=True)
    
    for file in path(BUILDDIR).files('*.js'):
        process_js(file)
    
    for file in path(BUILDDIR).files('*.js.map'):
        process_map(file)