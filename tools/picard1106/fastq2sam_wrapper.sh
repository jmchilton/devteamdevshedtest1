#!/bin/bash

if [ "$1" == "sam" ]
then
    output=$2.sam
else
    output=$2
fi

java -XX:DefaultMaxRAMFraction=1 -XX:+UseParallelGC -jar "$JAVA_JAR_PATH/FastqToSam.jar" SAMPLE_NAME="$3" READ_GROUP_NAME="$4" OUTPUT=$output ${*:5} 2>&1

if [ "$1" == "sam" ]
then
    mv $2.sam $2
fi
