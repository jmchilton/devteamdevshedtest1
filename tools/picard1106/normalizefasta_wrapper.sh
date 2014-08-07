#!/bin/bash
cp $2 $2.fasta
eval java -jar $JAVA_JAR_PATH/$1 INPUT=$2.fasta ${*:3}
rm -f $2.fasta
