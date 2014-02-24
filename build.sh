#!/usr/bin/env sh

TEST_FILES="counting issues misc options posix usage"

#
#   generate JSON
#
for srcFile in $TEST_FILES
do
    srcFilePath="./src/${srcFile}.cson"
    targetPath="${srcFile}.json"
      
    # For debugging
    #
    # cson2json "${srcFilePath}" > "${targetPath}"
    # cat "${targetPath}" | jsonpp > "${targetPath}.pp"
    # mv "${targetPath}.pp" "${targetPath}"
    
    ( cson2json "${srcFilePath}" | jsonpp > "${targetPath}" ) || echo "Error converting ${srcFile} to JSON"
    
done
