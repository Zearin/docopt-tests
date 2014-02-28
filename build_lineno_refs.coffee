# -*- coding: utf-8 -*-

###
#   Standard Library
###
fs = require('fs')
path = require('path')

###
#   External
###
_ = require('underscore')
CSON = require('cson')


#-------------------------------------------------------------------------------
#   CONSTANTS
#-------------------------------------------------------------------------------
PATH_TO_CSON = './src'
PATH_TO_JSON = ''


#-------------------------------------------------------------------------------
#   FILES
#-------------------------------------------------------------------------------
basename_filter = (fname) ->
  return path.extname(fname) is '.cson'

BASENAMES = _.filter(fs.readdirSync('./src'), basename_filter)
BASENAMES = _.map(BASENAMES, (fname) -> path.basename(fname, '.cson'))


#-------------------------------------------------------------------------------
#   DATA
#-------------------------------------------------------------------------------
for filename in BASENAMES
  csonfile = path.join(PATH_TO_CSON, "#{filename}.cson")
  jsonfile = path.join(PATH_TO_JSON, "#{filename}.json")
  
  csonSource = fs.readFileSync(csonfile, {encoding:'UTF-8'})
  jsonSource = fs.readFileSync(jsonfile, {encoding:'UTF-8'})
  
  csonData = CSON.parseFileSync(csonfile)
  
  
  
#-------------------------------------------------------------------------------
#   LINE NUMBERS
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
#   SANITY CHECK(s)
#-------------------------------------------------------------------------------