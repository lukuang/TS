#!/usr/bin/env perl

#
# generate the IDF hash for the work set
#
#

use strict;
use lib '/home/1546/perl15/model/';
use Getopt::Long;

my $script_name = "gen-idf-hash.pl";
my $usage = "$script_name [-v]\n";

my $verbose = 0;
GetOptions('verbose!' => \$verbose,
  ) or die $usage;

my %doc_list;
my %idf_hash;

my $raw_file = "/lustre/scratch/lukuang/Temporal_Summerization/xitong_method_data/top.2000";
my $idf_hash_file = "/lustre/scratch/lukuang/Temporal_Summerization/xitong_method_data/idf.hash.2000";

main();

sub main(){
  load_raw();
  save_idf_hash();
}

sub load_raw(){
  open RAW, $raw_file or die "Can't open `$raw_file': $!\n";
  print "Loading $raw_file\n";

  my %docs;
  my $doc = "";
  my $did;
  my $is_in_doc = 0;
  my $next_did=0;

  while(<RAW>){
    chomp;
    next if /^$/;
    
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

        $doc = trim($doc);
  
        my @terms = split / /, $doc;
        for my $term(@terms){
          $idf_hash{$term}{$did}++;
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

sub save_idf_hash(){
  open HASH, ">" . $idf_hash_file 
    or die "Can not open `$idf_hash_file': $!\n";
  print "Saving $idf_hash_file\n";

  for my $term(keys %idf_hash){
    for my $did(keys %{$idf_hash{$term}}){
      my $cnt = $idf_hash{$term}{$did};
      print HASH "$term $did $cnt\n";
    }
  }

  close HASH;
}

sub trim(){
  my $usage = "Usage: trim(\$str)\n";
  my $str = shift;

  unless(defined $str){
    print $usage;
    return "";
  }

  #undefline to space
  $str =~ s/\_/ /g;

  #remove non-word characters
  $str =~ s/\W+/ /g;

  #multiple spaces to single
  $str =~ s/\s+/ /g;

  #remove leading spaces
  $str =~ s/^\s//;

  #remove trailing spaces
  $str =~ s/\s$//;

  # to lowercase
  $str = lc $str;

  return $str;
}

