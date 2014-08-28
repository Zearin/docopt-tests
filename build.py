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

def process_file(file):
    file = path(file)
    
    # Cleanup
    lines = file.lines()
    
    if file.ext == '.js':
        lines[0]  = lines[0].replace('('  , '')
        lines[-3] = lines[-3].replace(');', '')
        lines     = lines[:-2]
    
    elif file.ext == '.map':
        lines[2] = lines[2].replace('.js"', '.json"')
    
    else:
        raise TypeError('UNEXPECTED FILE EXTENSION: ' + file.ext)
        
    file.write_lines(lines)
    
    # Rename the file
    newname = path.joinpath(BUILDDIR, file.basename().replace('.js', '.json'))
    file.rename(newname)
    
#--------------------------------------------------------------------------------

if __name__ == '__main__':
    import subprocess
    import sys
        
    try:
        # Convert *.cson to *.js
        subprocess.check_call(CMD, shell=True)
    
        # Convert *.js to *.json
        for file in path(BUILDDIR).files('*.js'):
            process_file(file)
    
        # Convert *.js.map to *.json.map
        for file in path(BUILDDIR).files('*.js.map'):
            process_file(file)
    
    except Exception as e:
        sys.exit(e)
    
    sys.exit(0)
