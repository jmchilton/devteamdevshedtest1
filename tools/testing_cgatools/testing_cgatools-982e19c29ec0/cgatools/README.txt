Provides galaxy tools for Complete Genomics' cgatools package -  http://www.completegenomics.com

This repository provides tools to execute functions of cgatools from Complete Genomics, Inc. 
and includes the cgatools 1.6 executable.
 
Reference genomes files for cgatools can be downloaded from Complete Genomics' ftp site:
ftp://ftp.completegenomics.com/ReferenceFiles/build37.crr
ftp://ftp.completegenomics.com/ReferenceFiles/build36.crr

Calibration files for cgatools can be downloaded from Complete Genomics' ftp site:
ftp://ftp.completegenomics.com/ScoreCalibrationFiles/var-calibration-v2.tgz

After copying the files in the desired locations follow the instructions below to register
the reference files with galaxy.




AUTOMATIC INSTALL

When prompted for a tool panel section to contain the installed tools create a new section 
called 'Complete Genomics - cgatools 1.6'.

After install create a cg_ccr_files.loc file in the tool-data directory of your Galaxy 
instance by copying the cg_ccr_files.loc.sample file. In cg_ccr_files.loc edit the path 
for the reference genome files (.crr files) downloaded from Complete Genomics' ftp site.

Restart Galaxy instance after editing cg_crr_files.loc.




MANUAL INSTALL

For manual install from compressed files move/copy the following files into your Galaxy instance:
directory tools/cgatools_1.6                        to   tools/
file      lib/galaxy/datatypes/completegenomics.py  to   lib/galaxy/datatypes/
file      tool-data/cg_crr_files.loc.sample         to   tool-data/cg_crr_files.loc

In cg_ccr_files.loc edit the path for the reference genome files (.crr files) downloaded 
from Complete Genomics' ftp site.

Paste from tool_config.xml.sample into the tool_config.xml of your Galaxy instance:
  <!-- 
    Copy the following section to tool_conf.xml file in your Galaxy distribution if you are
    adding Complete Genomics tools manually to your Galaxy instance
  -->
  <section name="Complete Genomics - cgatools 1.6" id="cg_cgatools1.6">
    <tool file="cgatools_1.6/listvariants.xml" />
    <tool file="cgatools_1.6/testvariants.xml" />
    <tool file="cgatools_1.6/listtestvariants.xml" />
    <tool file="cgatools_1.6/calldiff.xml" />
    <tool file="cgatools_1.6/snpdiff.xml" />
    <tool file="cgatools_1.6/junctiondiff.xml" />
    <tool file="cgatools_1.6/join.xml" />
    <tool file="cgatools_1.6/varfilter.xml" />
    <tool file="cgatools_1.6/mkvcf.xml" />
    <tool file="cgatools_1.6/evidence2sam.xml" />
  </section>
  <!-- End of copied section -->

Paste from tool_data_table_config.xml.sample into the tool_data_table_config.xml of your Galaxy instance:
    <!-- Start location of cgatools crr files -->
    <table name="cg_crr_files" comment_char="#">
        <columns>value, dbkey, name, path</columns>
        <file path="tool-data/cg_crr_files.loc" />
    </table>
    <!-- End Location of cgatools crr files -->

Paste from datatypes_conf.xml into the datatypes_conf.xml of your Galaxy instance:
    <!-- 
      Copy the following section to datatypes_conf.xml file in your Galaxy distribution if you are adding Complete Genomics tools manually to your Galaxy instance
    -->
    <!-- Start Complete Genomics Datatypes -->
    <datatype extension="cg_var" type="galaxy.datatypes.completegenomics:CG_Var" display_in_upload="true" />
    <datatype extension="cg_mastervar" type="galaxy.datatypes.completegenomics:CG_MasterVar" display_in_upload="true" />
    <datatype extension="cg_gene" type="galaxy.datatypes.completegenomics:CG_Gene" display_in_upload="true" />
    <!-- End Complete Genomics Datatypes -->
    <!-- End of copied section -->
    
Restart Galaxy instance.