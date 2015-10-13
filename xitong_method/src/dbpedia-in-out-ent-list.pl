#!/usr/bin/env perl

# generate the entity list by extract the neighbouring entities from the 
# DBPedia graph
#
# Version: 1.0.
#
# Usage: gen-ent-list.pl [-v]\n";
#        -v: verbose mode (default: no)
#
# 1.0  original release

use strict;
#use lib '/usa/xliu/usr/lib/site_perl/5.8.8/';
use Getopt::Long;
use String::CamelCase qw(decamelize wordsplit);

my $script_name = "dbpedia-in-out-ent-list.pl";
my $usage = "$script_name [-v]\n";

my $verbose = 0;
GetOptions('verbose!' => \$verbose,
    ) or die $usage;

# allow qrels and runfiles to be compressed with gzip
# @ARGV = map { /.gz$/ ? "gzip -dc $_ |" : $_ } @ARGV;

my $qent_match_dbpedia_file = "data/query-ent-dbpedia.map";
my $dbpedia_graph_file = "dbpedia/page_links_en.nt";
my $inc_ent_file = "data/in.ent.list";
my $out_ent_file = "data/out.ent.list";

my %qent_dbpedia_list;
my %all_dbpedia_list;
my %inc_ent_list;
my %out_ent_list;

main();

sub main(){
  load_qent_match_dbpedia();
  parse_dbpedia_graph();
  save_inc_ent_list();
  save_out_ent_list();
}

sub load_qent_match_dbpedia(){
  open FILE, $qent_match_dbpedia_file 
    or die "Can't open `$qent_match_dbpedia_file': $!\n";
  print "Loading $qent_match_dbpedia_file\n";

  while(<FILE>){
    chomp;
    next if /^$/;

    my ($qid, $qent, $uri) = split / : /;
    $uri = lc $uri;
    $qent_dbpedia_list{$qid}{$uri} = $qent;
    $all_dbpedia_list{$uri}{$qid} = $qent;
  }

  close FILE;
}

sub parse_dbpedia_graph(){
  open GRAPH, $dbpedia_graph_file 
    or die "Can't open `$dbpedia_graph_file': $!\n";
  print "Processing $dbpedia_graph_file\n";

  my $line_no = 0;
  while (<GRAPH>) {
    chomp;
    $line_no++;
    next if /^$/;

    my $line = $_;
    my ($subject, $predicate, $object)  = (undef, undef, undef);

    # parse it
    # if the data is surrounded with quotation mark ""
    if($line =~ m/<(.*)> <(.*)> "(.*)"/){
      $subject = $1;
      $predicate = $2;
      $object = $3;
    }
    # else all the fields were surrounded with <>
    elsif($line =~ m/<(.*)> <(.*)> <(.*)>/){
      $subject = $1;
      $predicate = $2;
      $object = $3;
    }else{
      print "Unknow format at at line $line_no:\n\t$line\n";
      next;
    }
    # make sure every field is valid, otherwise ignore it
    if((!defined $subject) or (!defined $object)){
      next;
    }

    $subject = lc $subject;
    # this is an out-going link
    if(defined $all_dbpedia_list{$subject}){
      next if $object =~ m/\%/;
      $out_ent_list{$subject}{$object} = 1;
    }

    $object = lc $object;
    # this is an in-coming link
    if(defined $all_dbpedia_list{$object}){
      next if $subject =~ m/\%/;
      $inc_ent_list{$object}{$subject} = 1;
    }

    #last if $line_no > 100000;
  }

  close GRAPH;
}

# save incomging entity list
sub save_inc_ent_list(){
  open LIST, ">" . $inc_ent_file 
    or die "Can't open `$inc_ent_file': $!\n";
  print "Saving $inc_ent_file\n";

  for my $object(keys %inc_ent_list){

    for my $subject(keys %{$inc_ent_list{$object}}){
      print LIST "$object : $subject\n";
    }
  }
  close LIST;
}

# save outgoing entity list
sub save_out_ent_list(){
  open LIST, ">" . $out_ent_file 
    or die "Can't open `$out_ent_file': $!\n";
  print "Saving $out_ent_file\n";

  for my $subject(keys %out_ent_list){

    for my $object(keys %{$out_ent_list{$subject}}){
      print LIST "$subject : $object\n";
    }
  }
  close LIST;
}

