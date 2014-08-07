#!/usr/bin/env python

"""
Runs Lastz
Written for Lastz v. 1.03.52.
"""
import optparse, os, subprocess, shutil, sys, tempfile, threading, time
from Queue import Queue

from galaxy import eggs
import pkg_resources
pkg_resources.require( 'bx-python' )
from bx.seq.twobit import *
from bx.seq.fasta import FastaReader
from galaxy.util.bunch import Bunch

STOP_SIGNAL = object()
SLOTS = 128

def stop_err( msg ):
    sys.stderr.write( "%s" % msg )
    sys.exit()

def stop_queues( lastz, combine_data ):
    """
    Send STOP_SIGNAL to all worker threads.  This method should only be called if
    an error has been encountered.
    """
    for t in lastz.threads:
        lastz.put( STOP_SIGNAL, True )
    combine_data.put( STOP_SIGNAL, True )


class BaseQueue( object ):

    def __init__( self, num_threads, slots=-1 ):
        """Initialize the queue and worker threads."""
        self.queue = Queue( slots )
        self.threads = []
        for i in range( num_threads ):
            worker = threading.Thread( target=self.run_next )
            worker.start()
            self.threads.append( worker )

    def run_next( self ):
        """Run the next job, waiting until one is available if necessary."""
        while True:
            job = self.queue.get()
            if job is STOP_SIGNAL:
                return self.shutdown()
            self.run_job( job )
            time.sleep( 1 )

    def run_job( self, job ):
        stop_err( 'Not Implemented' )

    def put( self, job, block=False ):
        """Add a job to the queue."""
        self.queue.put( job, block )

    def shutdown( self ):
        return


class LastzJobQueue( BaseQueue ):
    """
    A queue that runs commands in parallel.  Blocking is done so the queue will
    not consume much memory.
    """

    def run_job( self, job ):
        # Execute the job's command
        proc = subprocess.Popen( args=job.command, shell=True, stderr=subprocess.PIPE, )
        proc.wait()
        stderr = proc.stderr.read()
        proc.wait()
        if stderr:
            stop_queues( self, job.combine_data_queue )
            stop_err( stderr )
        job.combine_data_queue.put( job )


class CombineDataQueue( BaseQueue ):
    """
    A queue that concatenates files in serial.  Blocking is not done since this
    queue is not expected to grow larger than the command queue.
    """

    def __init__( self, output_filename, num_threads=1 ):
        BaseQueue.__init__( self, num_threads )
        self.CHUNK_SIZE = 2**20 # 1Mb
        self.output_file = open( output_filename, 'wb' )

    def run_job( self, job ):
        in_file = open( job.output, 'rb' )
        while True:
            chunk = in_file.read( self.CHUNK_SIZE )
            if not chunk:
                in_file.close()
                break
            self.output_file.write( chunk )
        for file_name in job.cleanup:
            os.remove( file_name )

    def shutdown( self ):
        self.output_file.close()
        return

def __main__():
    #Parse Command Line
    parser = optparse.OptionParser()
    parser.add_option( '', '--threads', dest='threads', help='The number of threads to use' )
    parser.add_option( '', '--ref_name', dest='ref_name', help='The reference name to change all output matches to' )
    parser.add_option( '', '--ref_source', dest='ref_source', help='Whether the reference is self, cached or from the history' )
    parser.add_option( '', '--ref_sequences', dest='ref_sequences', help='Number of sequences in the reference dataset' )
    parser.add_option( '', '--mirror', dest='mirror', help='Do or do not report mirror image of all gap-free alignments' )
    parser.add_option( '', '--source_select', dest='source_select', help='Whether to used pre-set or cached reference file' )
    parser.add_option( '', '--input1', dest='input1', help='The name of the reference file if using history or reference base name if using cached' )
    parser.add_option( '', '--input2', dest='input2', help='The reads file to align' )
    parser.add_option( '', '--strand', dest='strand', help='Which strand of the read to search, if specifying all parameters' )
    parser.add_option( '', '--match_reward', dest='match_reward', help='Score values for a match (reward)' )
    parser.add_option( '', '--match_penalty', dest='match_penalty', help='Score values for a mismatch (penalty), same as reward when not specified (but reward is)' )
    parser.add_option( '', '--gapped', dest='gapped', help='Perform gapped extension of HSPs (or seeds if gapped-free extension is not performed) after first reducing them to anchor points' )
    parser.add_option( '', '--gap_open', dest='gap_open', help='Score penalties for opening a gap' )
    parser.add_option( '', '--gap_extend', dest='gap_extend', help='Score penalties for extending a gap' )
    parser.add_option( '', '--ambiguous', dest='ambiguous', help='Treat as ambiguous nucleotides' )
    parser.add_option( '', '--step', dest='step', help='Offset between the starting positions of successive target words considered for potential seeds' )
    parser.add_option( '', '--masking', dest='masking', help='Dynamically mask the target sequence by excluding any positions that appear in too many alignments from further consideration for seeds' )
    parser.add_option( '', '--seed', dest='seed', help='Offset between the starting positions of successive target words considered for potential seeds' )
    parser.add_option( '', '--match_length', dest='match_length', help='Seeds require bp word of this length with matches in all positions' )
    parser.add_option( '', '--transition', dest='transition', help='Transition settings, affects the number of allowed transition substitutions in each seed' )
    parser.add_option( '', '--xdrop', dest='xdrop', help='Find HSPs using the xdrop extension method with the given termination threshold instead of using the exact match method' )
    parser.add_option( '', '--hspthresh', dest='hspthresh', help='Score threshold for the x-drop extension method' )
    parser.add_option( '', '--entropy', dest='entropy', help='Whether to adjust for entropy when qualifying HSPs in the x-drop extension method' )
    parser.add_option( '', '--chain', dest='chain', help='Perform chaining of HSPs with no penalties' )
    parser.add_option( '', '--ydrop', dest='ydrop', help='Set the threshold for terminating gapped extension' )
    parser.add_option( '', '--ytrim', dest='ytrim', help='Trim back to peak score if y-drop extension encounters end of sequence' )
    parser.add_option( '', '--gappedthresh', dest='gappedthresh', help='Threshold for gapped extension.  Alignments scoring lower are discarded.' )
    parser.add_option( '', '--filter', dest='filter', help='Filter alignments.' )
    parser.add_option( '', '--identity_min', dest='identity_min', help='Minimum for filtering alignments by their percent identity.' )
    parser.add_option( '', '--identity_max', dest='identity_max', help='Maximum for filtering alignments by their percent identity.' )
    parser.add_option( '', '--coverage_min', dest='coverage_min', help='Minimum for filtering alignments by how much of the input sequence they cover.' )
    parser.add_option( '', '--coverage_max', dest='coverage_max', help='Maximum for filtering alignments by how much of the input sequence they cover.' )
    parser.add_option( '', '--nmatch_min', dest='nmatch_min', help='Minimum for filtering alignments by how many bases they match.' )
    parser.add_option( '', '--nmismatch_max', dest='nmismatch_max', help='Maximum for filtering alignments by the number of mismatches.' )
    parser.add_option( '', '--trivial', dest='trivial', help='Do or do not output a trivial self-alignment block if the target and query sequences are identical.' )
    parser.add_option( '', '--inner', dest='inner', help='Perform additional alignment between the gapped alignment blocks using (presumably) more sensitive alignment parameters.' )
    parser.add_option( '', '--shortcuts_for_yasra', dest='shortcuts_for_yasra', help='Shortcut options to support the Yasra mapping assembler' )
    parser.add_option( '', '--out_format', dest='format', help='The format of the output file (sam, diffs, or tabular (general))' )
    parser.add_option( '', '--output', dest='output', help='The output file' )
    parser.add_option( '', '--lastzSeqsFileDir', dest='lastzSeqsFileDir', help='Directory of local lastz_seqs.loc file' )
    ( options, args ) = parser.parse_args()
    # Output version # of tool
    try:
        tmp = tempfile.NamedTemporaryFile().name
        tmp_stdout = open( tmp, 'wb' )
        proc = subprocess.Popen( args='lastz -v', shell=True, stdout=tmp_stdout )
        tmp_stdout.close()
        returncode = proc.wait()
        stdout = None
        for line in open( tmp_stdout.name, 'rb' ):
            if line.lower().find( 'version' ) >= 0:
                stdout = line.strip()
                break
        if stdout:
            sys.stdout.write( '%s\n' % stdout )
        else:
            raise Exception
    except:
        sys.stdout.write( 'Could not determine Lastz version\n' )

    if options.ref_name:
        ref_name = '[nickname=%s]' % options.ref_name
    else:
        ref_name = ''
    set_options = ''
    # Commonly-used preset options
    if options.source_select == 'pre_set':
        # Handle ref_source
        if options.ref_source == 'self':
            # --mirror is available only if ref_source selection is --self
            if options.mirror == 'yes':
                set_options += '--nomirror '
    else:
        # Full set of user-specified options
        # Handle ref_source
        if options.ref_source == 'self':
            # --mirror is available only if ref_source selection is --self
            if options.mirror == 'yes':
                set_options += '--nomirror '
        else:
            # Using --self automatically enables this option
            if options.trivial == 'no':
                set_options += '--notrivial '
        # Handle --match
        if options.match_reward not in [ "", "0" ]:
            if options.match_penalty in [ "", "0" ]:
                match_penalty = options.match_reward
            else:
                match_penalty = options.match_penalty
            set_options += '--match=%s,%s ' % ( options.match_reward, match_penalty )
        # Handle --gapped
        if options.gapped == 'yes':
            set_options += '--gapped '
            if options.gap_open not in [ "" ]:
                if options.gap_extend in [ "" ]:
                    set_options += '--gap=%s ' % options.gap_open
                else:
                    set_options += '--gap=%s,%s ' % ( options.gap_open, options.gap_extend )
            # Handle --ydrop
            if options.ydrop not in [ "", "0" ]:
                set_options += '--ydrop=%s ' % options.ydrop
            # Handle --ytrim
            if options.ytrim == 'no':
                set_options += '--noytrim '
            # Handle --gappedthresh
            if options.gappedthresh not in [ "", "0" ]:
                set_options += '--gappedthresh=%s ' % options.gappedthresh
            # Handle --inner
            if options.inner not in [ "" ]:
                set_options += '--inner=%s ' % options.inner
        else:
            set_options += '--nogapped '
        # Handle --step
        if options.step not in [ "", "0" ]:
            set_options += '--step=%s ' % options.step
        # Handle --masking
        if options.masking not in [ '0' ]:
            set_options += '--masking=%s ' % options.masking
        # Handle --seed
        if options.seed not in [ "no" ]:
            if options.seed == 'match':
                set_options += '--seed=match%s ' % options.match_length
            else:
                set_options += '--seed=%s ' % options.seed
        # Handle --transition
        if options.transition == '0':
            set_options += '--notransition '
        else:
            set_options += '--transition=%s ' % options.transition
        # Handle --xdrop
        if options.xdrop not in [ "", "0" ]:
            set_options += '--xdrop=%s ' % options.xdrop
        # handle --hspthresh
        if options.hspthresh not in [ "", "0" ]:
            set_options += '--hspthresh=%s ' % options.hspthresh
        # Handle --entropy
        if options.entropy == 'no':
            set_options += '--noentropy '
        else:
            set_options += '--entropy '
        # Handle --chain
        if options.chain == 'no':
            set_options += '--nochain '
        else:
            set_options += '--chain '
        # Handle --filter
        if options.filter not in [ "no" ]:
            if options.filter == 'identity':
                identity_min = options.identity_min
                if options.identity_max in [ "", "0" ] or options.identity_max <= identity_min:
                    identity_max = '100'
                else:
                    identity_max = options.identity_max
                set_options += '--filter=identity:%s..%s ' % ( identity_min, identity_max )
            elif options.filter == 'coverage':
                coverage_min = options.coverage_min
                if options.coverage_max in [ "", "0" ] or options.coverage_max <= coverage_min:
                    coverage_max = '100'
                else:
                    coverage_max = options.coverage_max
                set_options += '--filter=coverage:%s..%s ' % ( coverage_min, coverage_max )
            elif options.filter == 'nmatch':
                set_options += '--filter=nmatch:%s% ' % options.nmatch_min
            elif options.filter == 'nmismatch':
                set_options += '--filter=nmismatch:0..%s ' % options.nmismatch_max
    # Handle --strand
    set_options += '--strand=%s ' % options.strand
    # Handle --ambiguous
    if options.ambiguous not in [ "no" ]:
        set_options += '--ambiguous=%s ' % options.ambiguous
    # Handle --shortcuts_for_yasra
    if options.shortcuts_for_yasra not in [ 'none' ]:
        set_options += '--%s ' % ( options.shortcuts_for_yasra )
    # Specify input2 and add [fullnames] modifier if output format is diffs
    if options.format == 'diffs':
        input2 = '%s[fullnames]' % options.input2
    else:
        input2 = options.input2
    if options.format == 'tabular':
        # Change output format to general if it's tabular and add field names for tabular output
        format = 'general-'
        tabular_fields = ':score,name1,strand1,size1,start1,zstart1,end1,length1,text1,name2,strand2,size2,start2,zstart2,end2,start2+,zstart2+,end2+,length2,text2,diff,cigar,identity,coverage,gaprate,diagonal,shingle'
    elif options.format == 'sam':
        # We currently need to keep headers.
        format = 'sam'
        tabular_fields = ''
    else:
        format = options.format
        tabular_fields = ''
    # Set up our queues
    threads = int( options.threads )
    lastz_job_queue = LastzJobQueue( threads, slots=SLOTS )
    combine_data_queue = CombineDataQueue( options.output )
    if str( options.ref_source ) in [ 'history', 'self' ]:
        # Reference is a fasta dataset from the history or the dataset containing the target sequence itself,
        # so split job across the number of sequences in the dataset ( this could be a HUGE number ).
        try:
            # Ensure there is at least 1 sequence in the dataset ( this may not be necessary ).
            error_msg = "The reference dataset is missing metadata.  Click the pencil icon in the history item and 'auto-detect' the metadata attributes."
            ref_sequences = int( options.ref_sequences )
            if ref_sequences < 1:
                stop_queues( lastz_job_queue, combine_data_queue )
                stop_err( error_msg )
        except:
            stop_queues( lastz_job_queue, combine_data_queue )
            stop_err( error_msg )
        seqs = 0
        fasta_reader = FastaReader( open( options.input1 ) )
        while True:
            # Read the next sequence from the reference dataset
            seq = fasta_reader.next()
            if not seq:
                break
            seqs += 1
            # Create a temporary file to contain the current sequence as input to lastz
            tmp_in_fd, tmp_in_name = tempfile.mkstemp( suffix='.in' )
            tmp_in = os.fdopen( tmp_in_fd, 'wb' )
            # Write the current sequence to the temporary input file
            tmp_in.write( '>%s\n%s\n' % ( seq.name, seq.text ) )
            tmp_in.close()
            # Create a 2nd temporary file to contain the output from lastz execution on the current sequence
            tmp_out_fd, tmp_out_name = tempfile.mkstemp( suffix='.out' )
            os.close( tmp_out_fd )
            # Generate the command line for calling lastz on the current sequence
            command = 'lastz %s%s %s %s --format=%s%s > %s' % ( tmp_in_name, ref_name, input2, set_options, format, tabular_fields, tmp_out_name )
            # Create a job object
            job = Bunch()
            job.command = command
            job.output = tmp_out_name
            job.cleanup = [ tmp_in_name, tmp_out_name ]
            job.combine_data_queue = combine_data_queue
            # Add another job to the lastz_job_queue.  Execution will wait at this point if the queue is full.
            lastz_job_queue.put( job, block=True )
        # Make sure the value of sequences in the metadata is the same as the number of
        # sequences read from the dataset.  According to Bob, this may not be necessary.
        if ref_sequences != seqs:
            stop_queues( lastz_job_queue, combine_data_queue )
            stop_err( "The value of metadata.sequences (%d) differs from the number of sequences read from the reference (%d)." % ( ref_sequences, seqs ) )
    else:
        # Reference is a locally cached 2bit file, split job across number of chroms in 2bit file
        tbf = TwoBitFile( open( options.input1, 'r' ) )
        for chrom in tbf.keys():
            # Create a temporary file to contain the output from lastz execution on the current chrom
            tmp_out_fd, tmp_out_name = tempfile.mkstemp( suffix='.out' )
            os.close( tmp_out_fd )
            command = 'lastz %s/%s%s %s %s --format=%s%s >> %s' % \
                ( options.input1, chrom, ref_name, input2, set_options, format, tabular_fields, tmp_out_name )
            # Create a job object
            job = Bunch()
            job.command = command
            job.output = tmp_out_name
            job.cleanup = [ tmp_out_name ]
            job.combine_data_queue = combine_data_queue
            # Add another job to the lastz_job_queue.  Execution will wait at this point if the queue is full.
            lastz_job_queue.put( job, block=True )
    # Stop the lastz_job_queue.
    for t in lastz_job_queue.threads:
        lastz_job_queue.put( STOP_SIGNAL, True )
    # Although all jobs are submitted to the queue, we can't shut down the combine_data_queue
    # until we know that all jobs have been submitted to its queue.  We do this by checking
    # whether all of the threads in the lastz_job_queue have terminated.
    while threading.activeCount() > 2:
        time.sleep( 1 )
    # Now it's safe to stop the combine_data_queue.
    combine_data_queue.put( STOP_SIGNAL )

if __name__=="__main__": __main__()
