#!/usr/bin/env sh


#
#   clear 'all_tests.cson'
#
echo " " > ./src/all_tests.cson


#
#   rebuild 'all_tests.cson'
#
for srcFile in counting issues misc options posix usage
do
    cat "./src/${srcFile}.cson" >> ./src/all_tests.cson
    echo "\n\n"  >> ./src/all_tests.cson
done


#
#   generate JSON
#
for srcFile in counting issues misc options posix usage all_tests
do 
    cson2json "./src/${srcFile}.cson" | jsonpp > "${srcFile}.json"
done
