#!/bin/bash
reference_without_extension=${3%.*}
java -jar $JAVA_JAR_PATH/CreateSequenceDictionary.jar R=$3 O=$reference_without_extension.dict
eval java -Xmx2G -jar $JAVA_JAR_PATH/MergeBamAlignment.jar O=$1.$2 R=$3 ${*:4}
mv $1.$2 $1
