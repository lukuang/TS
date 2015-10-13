#!/usr/bin/env perl

# Generate the DBPedia entity list from the dump of labels from DBPedia
#
# Version: 1.0.
#
# Usage: gen-dbpedia-list.pl [-v]\n";
#        -v: verbose mode (default: no)
#
# 1.0  original release

use strict;
use lib '/home/1546/perl15/model/';
use Getopt::Long;
use String::CamelCase qw(decamelize wordsplit);

my $script_name = "gen-dbpedia-list.pl";
my $usage = "$script_name [-v]\n";

my $verbose = 0;
GetOptions('verbose!' => \$verbose,
    ) or die $usage;

# allow qrels and runfiles to be compressed with gzip
# @ARGV = map { /.gz$/ ? "gzip -dc $_ |" : $_ } @ARGV;

my $dbpedia_label_file = "/lustre/scratch/lukuang/Temporal_Summerization/xitong_method_data/labels_en.nt";
my $output_file = "/lustre/scratch/lukuang/Temporal_Summerization/xitong_method_data/all.ent.list";

my %ent_list;

main();

sub main(){
  parse_label_file();
  save_ent_list();
}

sub parse_label_file(){
  open DATA, $dbpedia_label_file 
    or die "Can't open `$dbpedia_label_file': $!\n";
  print "Processing $dbpedia_label_file\n";

  my $line_no = 0;
  while (<DATA>) {
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

    $object = decamelize($object);
    $object =~ s/\_+/ /g;
    $ent_list{$subject} = $object;
  }

  close DATA;
}

# save entity list
sub save_ent_list(){
  open OUTPUT, ">" . $output_file 
    or die "Can't open `$output_file': $!\n";
  print "Saving $output_file\n";

  for my $subject(keys %ent_list){
    my $object = $ent_list{$subject};
    print OUTPUT "$subject : $object\n";
  }
  close OUTPUT;
}

