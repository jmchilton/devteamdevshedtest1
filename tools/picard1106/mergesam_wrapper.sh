#!/bin/bash
eval java -Xmx2G -jar $JAVA_JAR_PATH/MergeSamFiles.jar O=$1.$2 ${*:3}
mv $1.$2 $1
