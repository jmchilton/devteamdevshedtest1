#!/bin/bash
eval java -Xmx2G -jar $JAVA_JAR_PATH/$1.jar O=$2.$3 ${*:4} 2>&1
mv $2.$3 $2
