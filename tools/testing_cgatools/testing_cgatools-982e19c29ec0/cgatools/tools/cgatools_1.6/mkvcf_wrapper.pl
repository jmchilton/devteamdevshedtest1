#!/usr/bin/perl
use strict;
use Getopt::Long;
use vars qw($opt_reference $opt_output @opt_input $opt_genomes $opt_source $opt_datasource $opt_fields $opt_nocalls $opt_calibration $opt_jctscore $opt_jctside $opt_jctdistance $opt_jctlength $opt_jctpriority $opt_jcttumor);
$| = 1; # set autoflush to screen

# This is a wrapper for the cgatools mkvcf function to run cgatools mkvcf in Galaxy.
# written 8-10-2012 by bcrain@completegenomics.com

#print join("\n", @ARGV), "\n";
&GetOptions("reference=s", "output=s", "input=s@", "genomes=i", "source=s", "datasource=s", "fields=s", "nocalls", "calibration:s", "jctscore=i", "jctside=i", "jctdistance=i", "jctlength=i", "jctpriority", "jcttumor");

my $command = "cgatools mkvcf --beta --reference $opt_reference --output $opt_output --source-names $opt_source";

if ($opt_datasource eq 'in')
{
	foreach my $file (@opt_input)
	{
		if ($opt_source eq 'masterVar') {$command .= " --master-var ";}
		elsif ($opt_source eq 'SV') {$command .= " --junction-file ";}
		else {die "there is an error in the logic: wrong source $opt_source for datasource $opt_datasource.\n";}
		$command .= $file
	}
}
elsif ($opt_datasource eq 'out')
{
	if ($opt_genomes == 1)
	{
		if ($opt_input[0] =~ m/masterVar/ and $opt_source eq 'masterVar')
		{
			-f $opt_input[0] or die "$opt_input[0] is not a valid file.\n";
			$command .= " --master-var $opt_input[0]";
		}
		elsif ($opt_input[0] =~ m/Junctions/ and $opt_source eq 'SV')
		{
			-f $opt_input[0] or die "$opt_input[0] is not a valid file.\n";
			$command .= " --junction-file $opt_input[0]";
		}
		else 
		{
			$opt_input[0] =~ s/\/$//;
			-d $opt_input[0] or die "$opt_input[0] is not a valid directory.\n";
			$command .= " --genome-root $opt_input[0]";
		}
	}
	else
	{
		-T $opt_input[0] or die "$opt_input[0] is not a valid file.\n";
		my $count = 0;
		foreach my $file (split /\s+/, `cat $opt_input[0]`)
		{
			$count ++;
			($opt_genomes == 2 and $count > 2) and die "The number of inputs in your list file cannot be greater than the number of genomes selected.\n";
			if ($file =~ m/masterVar/ and $opt_source eq 'masterVar')
			{
				-f $file or die "$file is not a valid file.\n";
				$command .= " --master-var ";
			}
			elsif ($file =~ m/Junctions/ and $opt_source eq 'SV')
			{
				-f $file or die "$file is not a valid file.\n";
				$command .= " --junction-file ";
			}
			else 
			{
				-d $file or die "$file is not a valid directory.\n";
				$command .= " --genome-root ";
			}
			$command .= $file
		}
	}
}
else
{die "there is an error in the logic: wrong datasource $opt_datasource.\n";}

if ($opt_calibration)
{
	(-r "$opt_calibration/0.0.0/metrics.tsv" or -r "$opt_calibration/version0.0.0/metrics.tsv") or die "This folder does not contain the calibration data\n";
	$command .= " --calibration-root $opt_calibration";
}

$opt_fields eq 'all' or $command .= " --field-names $opt_fields";
$opt_nocalls and $command .= " --include-no-calls";
$opt_jctscore and $command .= " --junction-score-threshold $opt_jctscore";
$opt_jctside and $command .= " --junction-side-length-threshold $opt_jctside";
$opt_jctdistance and $command .= " --junction-distance-tolerance $opt_jctdistance";
$opt_jctlength and $command .= " --junction-length-threshold $opt_jctlength";
$opt_jctpriority and $command .= " --junction-normal-priority";
$opt_jcttumor and $command .= " --junction-tumor-hc";

my $version = `cgatools | head -1`;
print "$version\n";
print "$command \n";

`$command`;