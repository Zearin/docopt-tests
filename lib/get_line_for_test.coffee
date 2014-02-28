# -*- coding: utf-8 -*-


###
Standard Library
###
fs = require('fs')
path = require('path')


###
External
###
_ = require('underscore')
CSON = require('cson')


#-------------------------------------------------------------------------------
#   CONSTANTS
#-------------------------------------------------------------------------------



#-------------------------------------------------------------------------------
#   FUNCTIONS
#-------------------------------------------------------------------------------
util= require('util')

inspect = (arg, colors = true, showHidden = true, depth = 8) ->
  options = {'colors':colors, 'showHidden': showHidden, 'depth':depth}
  util.inspect(arg, options)

###
Adapted from: https://groups.google.com/d/msg/nodejs/K2PWSV0m28g/mw71C2x6N6EJ
###
getLinesForFile = (filename) ->
   return fs.readFileSync(filename).toString().split('\n')


###
Adapted from: http://stackoverflow.com/a/6969486/180290
###
escapeRegExp = (str) ->
  return str.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&")


mapNamesToLines = (lines, names, sorted = false, linestart = 0, linestop = null, lineskips = []) ->
  _updateResult = (line, name, sorted) ->
    unless sorted is true
      result[name] = line
    else
      result.push( [name, line] )
  
  result = unless sorted then {} else []
  for name in names
    escapedName = escapeRegExp(name)
    pattern     = new RegExp('\\s*' + escapedName + '\\s*', 
                             'm')
    
    for line in lines[linestart..]
      if pattern.exec(line.trim())
        lineNumber = lines.indexOf(line)
        lineNumber += 1  # editor lines don't start at 0 :P
        _updateResult(lineNumber, name, sorted)
        break
  
  return result


mapTestFileLines = (filename) ->
  # File stuff
  basename  = path.basename(filename)
  cson      = CSON.parseFileSync(filename)
  lines     = getLinesForFile(filename)
  
  # Start building result
  result    = {}
  result[basename] = {}
  feature   = _.keys(cson).pop() # assumes 1 feature per file
  
  ###
    *
    * TODO:
    *   Idea:
    * 
    *     1. Build the object hierarchy, marking lines only for scenarios.  
    *        (Scenarios must be unique; usages are unique within their scope, but may have dupes within a file)
    *        1.1. Determine `linestart`,`linestop` ranges for scenarios.
    *     
    *     2. Determine line numbers for usages (scoped by parent line ranges).
    *        2.1 Determine `linestart`,`linestop` ranges for usages.
    *     
    *     3. Determine line numbers for argv/inputs (scoped by parent line ranges).
    *        3.1 ...PROFIT   :D   :D   :D
    *
  ###
  
  # Scenarios
  _populateScenarios = () ->
    scenarioNames   = _.keys(cson[feature])
    scenarioNames   = _.without(scenarioNames, '__desc')
    scenarioLineMap =  mapNamesToLines(lines, scenarioNames)
    # sLines    = _.values(scenarioLineMap )
    
    for name in scenarioNames
      #console.log "#{name}"
      line = scenarioLineMap[name]
      # nextScenarioLine = _.filter(sLines, (x) -> x > line)
      # nextScenarioLine = _.min(nextScenarioLine)
      result[basename][name] = {'__line':line}
      scenario     = cson[feature][name]
      _populateUsages(name, scenario, linestart=line)
      console.log '\n'
      
  
  _populateUsages = (scenarioName, scenario, linestart) ->
    usageNames   = _.keys(scenario)
    usageLineMap = mapNamesToLines(lines, usageNames, linestart=linestart)
    
    for name in usageNames
      #console.log "\t#{name}"
      line    = usageLineMap[name]
      usage   = scenario[name]
      result[basename][scenarioName][name]  = {'__line':line}
      _populateTests(name, usage, linestart=line, resultTarget=result[basename][scenarioName][name])
  
  _populateTests = (usageName, usage, linestart, resultTarget) ->
    testInputs = _.indexBy(usage, 'input')
    testInputs = _.keys(testInputs)
    testMap    = mapNamesToLines(lines, testInputs, linestart=linestart)
    #console.log testMap
    for argv in testInputs
      line = testMap[argv]
      resultTarget[argv] = {'__line':line}

  _populateScenarios()
  
  
  
  
  return JSON.stringify(result)


#-------------------------------------------------------------------------------
#   ...
#-------------------------------------------------------------------------------


console.log inspect(JSON.parse(mapTestFileLines('src/counting.cson')), depth=99)