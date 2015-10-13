#!/usr/bin/env perl

#
# genreate the working set given top-K retrieval list
#
#

use strict;
use lib '/home/1546/perl15/model/';
use Getopt::Long;

my $script_name = "gen-workset.pl <ret_list> <save>";
my $usage = "$script_name [-v]\n";

my $verbose = 0;
GetOptions('verbose!' => \$verbose,
  ) or die $usage;

my %ret_list;
my %doc_list;

my $raw_file = "corpus/raw";

my $ret_list_file = shift or die $usage;
my $save_file = shift or die $usage;

main();

sub main(){
  load_ret_list();
  load_raw();
  save_corpus();
}

sub load_ret_list(){
  open FILE, $ret_list_file or die "Can't open `$ret_list_file': $!\n";
  print "Loading $ret_list_file\n";

  while(<FILE>){
    chomp;
    next if /^$/;

    my ($qid, undef, $did, $rank, $score, undef) = split;
    $ret_list{$did} = 1;
  }

  close FILE;
}

sub load_raw(){
  open RAW, $raw_file or die "Can't open `$raw_file': $!\n";
  print "Loading $raw_file\n";

  my %docs;
  my $doc = "";
  my $did;
  my $is_in_doc = 0;

  while(<RAW>){
    chomp;
    next if /^$/;
    my $next_did = 0;

    if($_ =~ m/<DOCNO>\s*(.*)\s*<\/DOCNO>/){
      $did = $1;
      $did =~ s/^\s+//;
      $did =~ s/\s+$//;
      next;
    }
    elsif($_=~m/<DOCNO>/){
	$next_did = 1;
        next;
    }
    elsif($next_did ==1 and $_=~m/(\S+)/ ){
      $did = $1;
      $did =~ s/^\s+//;
      $did =~ s/\s+$//;
      $next_did = 0;
      next;
    }
   
    if($_ =~ m/<DOC>/){
      $is_in_doc = 1;
      next;
    }

    if(1 == $is_in_doc){
      if($_ =~ m/<\/DOC>/){
        $is_in_doc = 0;

        # check whether any entity is mapped to the document
        if(defined $ret_list{$did}){
          $doc_list{$did} = $doc;
        }

        # reset the intermediate variables
        $doc = "";

        next;
      }else{
        $doc = $doc . $_ ."\n";
      }
    }
  }

  close RAW;
}

sub save_corpus(){
  open CORPUS, ">" . $save_file 
    or die "Can't open `$save_file': $!\n";
  print "Saving $save_file\n";

  for my $did(sort {$a cmp $b} keys %doc_list){
    my $doc = $doc_list{$did};

    next if !defined $doc;
    print CORPUS "<DOC>\n";
    print CORPUS "<DOCNO> $did <\/DOCNO>\n";
    #print CORPUS "<TEXT>\n";
    print CORPUS "\n$doc\n\n";
    #print CORPUS "<\/TEXT>\n";
    print CORPUS "<\/DOC>\n";
  }

  close CORPUS;
}

