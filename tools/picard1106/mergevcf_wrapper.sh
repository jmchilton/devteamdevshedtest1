#!/bin/bash
#index all vcfs
args=""
for file in  ${*:2}
do
	cp $file $file.vcf
	java -Xmx1500m  -jar `dirname $0`/igvtools.jar index $file.vcf
	args="$args I=$file.vcf"
done

eval java -Xmx2G -jar $JAVA_JAR_PATH/MergeVcfs.jar QUIET=True O=$1 $args

for file in  ${*:2}
do
	rm -f $file.vcf
	rm -f $file.vcf.idx
done
