#!/usr/bin/env perl

use strict;

use lib '/home/1546/perl15/model/';
use Getopt::Long;

#
# Use the relation language model to expand the query language model for
# lemur
#

my $script_name = "rel-exp-query-v2.pl";
my $usage = "$script_name [-v] <ent_list> <num_ent> <lambda> <query_lm> <save>\n";

my $verbose = 0;
GetOptions('verbose!' => \$verbose,
  ) or die $usage;


# the decay of importance w.r.t. the rank
my $decay = 0;
# the number of terms tp represent the language model
my $term_num = 100;

my $ret_list_file = "/lustre/scratch/lukuang/Temporal_Summerization/TS/xitong_method/ret/top.2000";
my $corpus_file = "/lustre/scratch/lukuang/Temporal_Summerization/xitong_method_data/transform";

my $doc_dbpedia_map_in_file = "data/doc-dbpedia-map/in";
my $doc_dbpedia_map_out_file = "data/doc-dbpedia-map/out";
my $query_ent_map_file = "data/query-ent-doc.map";

my %rel_ent_list;
my %ent_list;
my %ent_rev_list;
my %e2d_map;

my %qent_doc_map;
my %doc_qent_map;

my %ent_rel_lm;

my %query_map;
my %query_lm;
my %intep_lm;

my %ret_list;
my %corpus;

my $ent_list_file = shift;
my $num_ent = shift;
my $lambda = shift;
my $query_lm_file = shift;
my $save_file = shift;

unless(defined $ent_list_file and defined $num_ent 
    and defined $lambda and defined $query_lm_file){
  die $usage;
}
if($lambda < 0 or $lambda > 1){
  die "Invalid lambda, it must between 0 and 1\n";
}
if($num_ent <=0){
  die "num_ent must be greater than 0\n";
}

unless(defined $save_file){
  $save_file = "./tune/query/rel.exp";
}
main();

sub main(){
  load_rel_ent_list();
  load_e2d_map($doc_dbpedia_map_in_file);
  load_e2d_map($doc_dbpedia_map_out_file);

  load_query_ent_map();
  load_query_lm();

  load_ret_list();
  load_corpus();

  do_interpolation();
  save_query_lm();
}

# load the ranked entity list
sub load_rel_ent_list(){
  open RES, $ent_list_file or die "can't open $ent_list_file: $!\n";
  print "Loading $ent_list_file\n";

  my %dup_check;
  my $rank = 1;
  my %res_hash;
  while (<RES>) {
    chomp;
    next if /^$/;
    
    my ($qid, $rank, $ent, $score, $uri) = split / : /;
    if(exists $dup_check{$qid}{$ent}){
      print "Duplicate record: $qid-$rank-$ent\n" if $verbose;
      next;
    }
    $dup_check{$qid}{$ent} = 1;

    $rel_ent_list{$qid}{$rank} = $uri;
    $ent_list{$uri} = $ent;
    $ent_rev_list{$ent} = $uri;
  }
  close RES;
}

sub load_e2d_map(){
  my $usage = "Usage: load_e2d_map(\$map_file)\n";
  my $map_file = shift or die $usage;

  open MAP, $map_file or die "Can not open `$map_file': $!\n";
  print "Lading $map_file\n";

  while(<MAP>){
    chomp;
    next if /^$/;

    my($uri, $ent, $did) = split / : /;
    $ent_list{$uri} = $ent;
    $ent_rev_list{$ent} = $uri;
    $e2d_map{$uri}{$did} = 1;
  }

  close MAP;
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

# load the initial query LM
sub load_query_lm(){
  open FILE, $query_lm_file or die "Can't open `$query_lm_file': $!\n";
  print "Loading $query_lm_file\n";

  my $qid = 0;
  my $num = 0;
  while(<FILE>){
    chomp;
    next if /^$/;

    if($_ =~ m/^(\d+) (\d+)$/){
      $qid = $1;
      $num = $3;
      next;
    }
    my ($term, $prob) = split;
    $query_lm{$qid}{$term} = $prob;
  }

  close FILE;
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

sub load_corpus(){
  open CORPUS, $corpus_file or die "can't open $corpus_file: $!\n";
  print "Loading $corpus_file\n";

  while (<CORPUS>) {
    chomp;
    next if /^$/;

    my ($did, $doc) = split / : /;
    next if !defined $ret_list{$did};
    $doc = trim($doc);
    $corpus{$did} = $doc;
  }

  close CORPUS;
}

sub do_interpolation(){
  for my $qid(sort {$a<=>$b} keys %query_lm){
    print "Topic $qid \n";

    my %rel_lm;
    for my $rank(sort {$a<=>$b} keys %{$rel_ent_list{$qid}}){
      my $weight = 1 - $decay * $rank;
      last if $weight < 0;
      last if $rank > $num_ent;

      my $ent_uri = $rel_ent_list{$qid}{$rank};
      my %lm = %{est_ent_rel_lm($qid, $ent_uri)};

      for my $term(keys %lm){
        if(defined $rel_lm{$term}){
          $rel_lm{$term} += $lm{$term};
        }else{
          $rel_lm{$term} = $lm{$term};
        }
      }
    }

    # normalize it
    my $sum = 0.00000001;
    for my $term(keys %rel_lm){
      $sum += $rel_lm{$term};
    }
    for my $term(keys %rel_lm){
      $rel_lm{$term} /= $sum;
    }

    # now we can apply the linear interpolation
    my %terms;
    for my $term(keys %{$query_lm{$qid}}){
      $terms{$term} = 1;
    }
    for my $term(keys %rel_lm){
      $terms{$term} = 1;
    }

    for my $term(keys %terms){
      my $w_rel = 0;
      if(defined $rel_lm{$term}){
        $w_rel = $rel_lm{$term};
      }
      my $w_in = 0;
      if(defined $query_lm{$qid}{$term}){
        $w_in = $query_lm{$qid}{$term};
      }
      my $w = $w_rel * $lambda + $w_in * ( 1 - $lambda);
      $intep_lm{$qid}{$term} = $w;
    }
    #last;
  }
}

# estimate the relation language model between a query and an entity
sub est_ent_rel_lm(){
  my $usage = "est_ent_rel_lm(\$qid, \$uri)\n";
  my $qid = shift;
  my $uri = shift;

  unless(defined $qid and defined $uri){
    die $usage;
  }

  my %lm;
  unless(defined $qent_doc_map{$qid} and defined $e2d_map{$uri}){
    return \%lm;
  }

  # if we have esitmated it previously, return it directly
  if(defined $ent_rel_lm{$qid}{$uri}){
    for my $term(keys %{$ent_rel_lm{$qid}{$uri}}){
      $lm{$term} = $ent_rel_lm{$qid}{$uri}{$term};
    }
    return \%lm;
  }

  my %e_doc;
  for my $did(keys %{$qent_doc_map{$qid}}){
    $e_doc{$did} = 1;
  }
  my %re_doc;
  for my $did(keys %{$e2d_map{$uri}}){
    $re_doc{$did} = 1;
  }

  my %com_doc;
  for my $did(keys %e_doc){
    if(defined $re_doc{$did}){
      $com_doc{$did} = 1;
    }
  }

  for my $did(keys %com_doc){
    unless(defined $corpus{$did}){
      print "No document: $did\n";
      next;
    }
    my $doc = $corpus{$did};
    my @term_array = split / /, $doc;
    for my $term(@term_array){
      if(defined $lm{$term}){
        $lm{$term}++;
      }else{
        $lm{$term} = 1;
      }
    }
  }
    
  # normalize it
  my $sum = 0.00000001;
  for my $term(keys %lm){
    $sum += $lm{$term};
  }
  for my $term(keys %lm){
    $lm{$term} = $lm{$term} / $sum;
  }
 
  # store it in the cache
  for my $term(keys %lm){
    $ent_rel_lm{$qid}{$uri}{$term} = $lm{$term};
  }

  return \%lm;
}

sub save_query_lm(){
  open QUERY, ">" . $save_file or die "Can't open `$save_file': $!\n";
  print "Saving $save_file\n";

  for my $qid(sort {$a<=>$b} keys %intep_lm){
    my $num = scalar keys %{$intep_lm{$qid}};
    if($num > $term_num){
      print QUERY "$qid $term_num\n";
    }else{
      print QUERY "$qid $num\n";
    }

    my $sofar = 0;
    for my $term(sort {$intep_lm{$qid}{$b}<=>$intep_lm{$qid}{$a}} 
      keys %{$intep_lm{$qid}}){

      last if ++$sofar > $term_num;
      my $w = $intep_lm{$qid}{$term};
      print QUERY "$term $w\n";
    }
  }
 
  close QUERY;
}

sub trim(){
  my $usage = "Usage: trim(\$str)\n";
  my $str = shift;

  if(!defined $str){
    die $usage;
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

  # to lower case
  $str = lc $str;

  return $str;
}

