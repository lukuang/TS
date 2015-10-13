#!/usr/bin/env perl

#
# match the query entities with the documents
#

use strict;
use lib '/home/1546/perl15/model/';
use Getopt::Long;
use String::CamelCase qw(decamelize wordsplit);

my $script_name = "qent-match-doc.pl";
my $usage = "$script_name [-v]\n";

my $verbose = 0;
GetOptions('verbose!' => \$verbose,
  ) or die $usage;

my %ret_list;
my %doc_list;
my %query_ent_list;
my %query_wiki_list;
my %ent_match_list;

my $ret_list_file = "ret/top.2000";
my $query_ent_list_file = "data/query-ent-dbpedia.map";
my $raw_file = "/lustre/scratch/lukuang/Temporal_Summerization/xitong_method_data/raw";

my $ent_match_file = "data/query-ent-doc.map";

main();

sub main(){
  load_ret_list();
  load_query_ent_list();
  load_raw();
  do_match();
  save_ent_match();
}

sub load_ret_list(){
  open FILE, $ret_list_file or die "Can't open `$ret_list_file': $!\n";
  print "Loading $ret_list_file\n";

  while(<FILE>){
    chomp;
    next if /^$/;

    my ($qid, undef, $did, $rank, $score, undef) = split;
    $ret_list{$qid}{$did} = $rank;
  }

  close FILE;
  print "there are ".scalar( keys %ret_list)." queries";
}

sub load_query_ent_list(){
  open FILE, $query_ent_list_file or die "Can't open `$query_ent_list_file': $!\n";
  print "Loading $query_ent_list_file\n";

  while(<FILE>){
    chomp;
    next if /^$/;

    my ($qid, $qent, $uri) = split / : /;
    
    # process the DBPedia URI
    my $wiki = $uri;
    if($uri =~ m|http://dbpedia.org/resource/(.*)|){
      $wiki = $1;
      $wiki = decamelize($wiki);
      $wiki = trim($wiki);
    }
    
    $qent = trim($qent);
    $wiki = trim($wiki);
    $query_ent_list{$qid}{$qent} = 1;
    $query_wiki_list{$qid}{$wiki} = 1;
  }

  print "there are ".scalar( keys %query_ent_list)." queries";
  close FILE;
}

sub load_raw(){
  open RAW, $raw_file or die "Can't open `$raw_file': $!\n";
  print "Loading $raw_file\n";

  my %docs;
  my $doc = "";
  my $did;
  my $is_in_doc = 0;
  my $next_did = 0;
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

        # save the doc
        $doc_list{$did} = $doc;

        # reset the intermediate variables
        $doc = "";

        next;
      }else{
        $doc = $doc . $_ ."\n";
      }
    }
  }
  printf("there are %d documents\n",scalar (keys %doc_list));
  close RAW;
}

sub do_match(){
  print "Doing entity match\n";

  for my $qid(sort {$a<=>$b} keys %ret_list){
    for my $did(keys %{$ret_list{$qid}}){
      unless(defined $doc_list{$did}){
        print "I can not find $did for query#$qid\n";
        next;
      }
      my $doc = $doc_list{$did};
      $doc = trim($doc);
      $doc = " $doc ";

      # first, try to match the query entities
      for my $ent(keys %{$query_ent_list{$qid}}){
        if($doc =~ m/ $ent /){
          $ent_match_list{$qid}{$did}{ENT} = $ent;
        }
      }
      # then, try to match the query wiki
      for my $wiki(keys %{$query_wiki_list{$qid}}){
        if($doc =~ m/ $wiki /){
          $ent_match_list{$qid}{$did}{WIKI} = $wiki;
        }
      }
    }
  }
}

sub save_ent_match(){
  open ENT_MATCH, ">" . $ent_match_file 
    or die "Can't open `$ent_match_file': $!\n";
  print "Saving $ent_match_file\n";

  for my $qid(sort {$a<=>$b} keys %ent_match_list){
    for my $did(keys %{$ent_match_list{$qid}}){
      for my $type(keys %{$ent_match_list{$qid}{$did}}){
        my $match = $ent_match_list{$qid}{$did}{$type};
        print ENT_MATCH "$qid--$did--$type--$match\n";
      }
    }
  }

  close ENT_MATCH;
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

