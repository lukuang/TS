#!/usr/bin/env perl

#
# match the dbpedia entities with document
#
# This should take very long time to process because of the large volumn of
# data and high time complexity
#

use strict;
use Getopt::Long;

my $script_name = "doc-match-dbpedia.pl <dbpedia_ent_list> <filter_ent_list> <ent_match>";
my $usage = "$script_name [-v]\n";

my $verbose = 0;
GetOptions('verbose!' => \$verbose,
  ) or die $usage;

my %qent_doc_map;
my %doc_qent_map;
my %doc_list;
my %filter_ent_list;

my $query_ent_map_file = "data/query-ent-doc.map";
my $raw_file = "corpus/top.2000";

my $dbpedia_ent_list_file = shift or die $usage;
my $filter_ent_list_file = shift or die $usage;
my $ent_match_file = shift or die $usage;

main();

sub main(){
  load_query_ent_map();
  load_filter_ent_list();
  load_raw();
  load_dbpedia_ent_list();
}

sub load_query_ent_map(){
  open MAP, $query_ent_map_file or die "Can't open `$query_ent_map_file': $!\n";
  print "Loading $query_ent_map_file\n";

  while(<MAP>){
    chomp;
    next if /^$/;

    my ($qid, $did, $type, $ent) = split /--/;
    $qent_doc_map{$qid}{$did}{$type} = $ent;
    $doc_qent_map{$did}{$qid}{$type} = $ent;
  }

  close MAP;
}

sub load_filter_ent_list(){
  open LIST, $filter_ent_list_file or die "Can't open `$filter_ent_list_file': $!\n";
  print "Loading $filter_ent_list_file\n";

  while(<LIST>){
    chomp;
    next if /^$/;

    my ($uri1, $uri2) = split / : /;
    $uri1 = lc $uri1;
    $uri2 = lc $uri2;
    $filter_ent_list{$uri1} = 1;
    $filter_ent_list{$uri2} = 1;
  }

  close LIST;
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

    if($_ =~ m/<DOCNO>(.*)<\/DOCNO>/){
      $did = $1;
      $did =~ s/^\s+//;
      $did =~ s/\s+$//;
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
        if(defined $doc_qent_map{$did}){
          $doc = trim($doc);
          $doc = " $doc ";
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

sub load_dbpedia_ent_list(){
  open DBPEDIA, $dbpedia_ent_list_file
    or die "Can not open `$dbpedia_ent_list_file': $!\n";
  print "Loading $dbpedia_ent_list_file\n";

  my $so_far = 0;
  while(<DBPEDIA>){
    chomp;
    next if /^$/;

    my ($db_uri, $db_ent) = split / : /;
    $db_uri = lc $db_uri;
    next if !defined $filter_ent_list{$db_uri};

    my $ent = trim($db_ent);
    my %match_list = ();

    for my $did(keys %doc_list){
      my $doc = $doc_list{$did};
      if($doc =~ m/ $ent /){
        $match_list{$did} = 1;
      }
    }

    my $match_num = scalar keys %match_list;
    next if 0 == $match_num;

    save_match_list($db_uri, $db_ent, \%match_list);

    # free up the memory
    for (keys %match_list){
      delete $match_list{$_};
    }

    print "$so_far\n";
    ++$so_far;
  }

  close DBPEDIA;
}

# to avoid exhausting the memoery, we save the match list whenever called
sub save_match_list(){
  my $usage = "Usage: save_match_list(\$db_uri, \$db_ent, \%match_list)\n";
  my $db_uri = shift;
  my $db_ent = shift;
  my $match_list_ref = shift;

  unless(defined $db_uri and defined $db_ent and defined $match_list_ref){
    print $usage;
    return;
  }

  my %matched_list = %{$match_list_ref};

  # deside to append to the file or create instead
  if(-f $ent_match_file){
    open ENT_MATCH, ">>" . $ent_match_file 
      or die "Can not open `$ent_match_file': $!\n";
  }else{
    open ENT_MATCH, ">" . $ent_match_file 
      or die "Can not open `$ent_match_file': $!\n";
  }

  for my $did(keys %matched_list){
    print ENT_MATCH "$db_uri : $db_ent : $did\n";
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

