#!/usr/bin/env perl

use strict;
use lib '/home/1546/perl15/model/';
use Getopt::Long;

#
# Expand the query langauge model using the retrieved entities, IDF values are
# incorporated into the language model estimation process
#

my $script_name = "ent-query-exp-v3.pl";
my $usage = "$script_name [-v] <ent_list> <num_ent> <lambda> <input_lm> <save>\n";

my $verbose = 0;
GetOptions('verbose!' => \$verbose,
  ) or die $usage;

my %input_lm;
my %ent_list;
my %intep_lm;

my %idf_list;

# all related to stemming
my $stem_app = "./api/krovetz-stemmer";
my %stem_cache;
my $stem_cache_file = "./stem/cache";

my $ent_list_file = shift;
my $num_ent = shift;
my $lambda = shift;
my $input_lm_file = shift;
my $save_file = shift;


unless(defined $ent_list_file and defined $num_ent 
    and defined $lambda and defined $input_lm_file){
  die $usage;
}
if($lambda < 0 or $lambda > 1){
  die "Invalid lambda, it must between 0 and 1\n";
}
if($num_ent <=0){
  die "num_ent must be greater than 0\n";
}

unless(defined $save_file){
  $save_file = "./tune/query/ent.exp";
}

main();

sub main(){
  #load_stem_cache();
  load_query_lm();
  load_ent_list();
  do_interpolation();
  save_query();
  #save_stem_cache();
}

sub load_query_lm(){
  open FILE, $input_lm_file or die "Can't open `$input_lm_file': $!\n";
  print "Loading $input_lm_file\n";
  my $qid = 0;
  my $num = 0;
  while(<FILE>){
    chomp;
    next if /^$/;

    if($_ =~ m/^(\d+) (\d+)$/){
      $qid = $1;
      $num = $2;
      next;
    }
    my ($term, $prob) = split;
    $input_lm{$qid}{$term} = $prob;
  }

  close FILE;
}

sub load_ent_list(){
  open RES, $ent_list_file or die "can't open $ent_list_file: $!\n";
  print "Loading $ent_list_file\n";

  my %dup_check;
  my $rank = 1;
  while (<RES>) {
    chomp;
    next if /^$/;
    
    my ($qid, $rank, $entStr, $score, $uri, $idf) = split / : /;
    next if $rank > $num_ent;

    if(exists $dup_check{$qid}{$entStr}){
      print "Duplicate record: $qid-$rank-$entStr\n" if $verbose;
      next;
    }
    $dup_check{$qid}{$entStr} = 1;

    $entStr = trim($entStr);
    $ent_list{$qid}{$rank} = $entStr;
    if(defined $idf){
      $idf_list{$qid}{$rank} = $idf;
    }else{
      die "IDF value undefined!\n";
    }
  }
  close RES;
}

sub do_interpolation(){
  for my $qid(sort {$a<=>$b} keys %input_lm){
    print "Topic $qid \n";

    # normalize the IDF weight list
    my $max_idf = 0;
    for my $rank(sort {$a<=>$b} keys %{$idf_list{$qid}}){
      my $idf = $idf_list{$qid}{$rank};
      $max_idf = $idf if $max_idf < $idf;
    }
    if(0 == $max_idf){
      for my $rank(sort {$a<=>$b} keys %{$idf_list{$qid}}){
        $idf_list{$qid}{$rank} = 1;
      }
    }else{
      for my $rank(sort {$a<=>$b} keys %{$idf_list{$qid}}){
        $idf_list{$qid}{$rank} = $idf_list{$qid}{$rank} / $max_idf;
      }
    }

    # estimate the entity language model first
    my %ent_lm;
    for my $rank(sort {$a<=>$b} keys %{$ent_list{$qid}}){
      my $weight = $idf_list{$qid}{$rank};
      last if $weight < 0;
      last if $rank > $num_ent;

      my $ent = $ent_list{$qid}{$rank};
      my @terms = split / /, $ent;
      
      for my $term(@terms){
        #$term = stem($term);
        if(defined $ent_lm{$term}){
          $ent_lm{$term} += $weight;
        }else{
          $ent_lm{$term} = $weight;
        }
      }
    }

    # normalize the entity language model
    my $sum = 0.00000001;
    for my $term(keys %ent_lm){
      $sum += $ent_lm{$term};
    }
    for my $term(keys %ent_lm){
      $ent_lm{$term} = $ent_lm{$term} / $sum;
    }

    # now we can apply the linear interpolation
    my %terms;
    for my $term(keys %{$input_lm{$qid}}){
      $terms{$term} = 1;
    }
    for my $term(keys %ent_lm){
      $terms{$term} = 1;
    }

    for my $term(keys %terms){
      my $w_ent = 0;
      if(defined $ent_lm{$term}){
        $w_ent = $ent_lm{$term};
      }
      my $w_in = 0;
      if(defined $input_lm{$qid}{$term}){
        $w_in = $input_lm{$qid}{$term};
      }
      my $w = $w_ent * $lambda + $w_in * ( 1 - $lambda);
      $intep_lm{$qid}{$term} = $w;
    }
  }
}

sub save_query(){
  open QUERY, ">" . $save_file or die "Can't open `$save_file': $!\n";
  print "Saving $save_file\n";

  for my $qid(sort {$a<=>$b} keys %intep_lm){
    my $num = scalar keys %{$intep_lm{$qid}};
    print QUERY "$qid $num\n";
    for my $term(sort {$intep_lm{$qid}{$b}<=>$intep_lm{$qid}{$a}} 
      keys %{$intep_lm{$qid}}){
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

  $str = lc $str;
  return $str;
}

# all related to stemming
sub load_stem_cache(){
  open CACHE, $stem_cache_file 
    or die "Can not open `$stem_cache_file': $!\n";
  print "Loading $stem_cache_file \n";

  while(<CACHE>){
    chomp;
    next if /^$/;

    my($term, $stem) = split;
    $stem_cache{$term} = $stem;
  }

  close CACHE;
}

sub save_stem_cache(){
  open CACHE, ">" . $stem_cache_file 
    or die "Can not open `$stem_cache_file': $!\n";
  print "Saving $stem_cache_file \n";

  for my $term(keys %stem_cache){
    my $stem = $stem_cache{$term};
    print CACHE "$term $stem\n";
  }

  close CACHE;
}

# apply stemming
sub stem(){
  my $usage = "Usage: stem(\$input)\n";
  my $input = shift;

  my $output = "";
  unless(defined $input){
    print $usage;
    return $output;
  }

  if(defined $stem_cache{$input}){
    $output = $stem_cache{$input};
    return $output;
  }

  my $stem = "$stem_app 2>/dev/null";
  my $stem_cmd = $stem . " " . $input . " |";
  #print "$stem_cmd\n";
 
  open STEM_PIPE, $stem_cmd or die "Can not open `$stem_cmd':$!\n";
  #print "Extracting $doc_id\n";
  while(<STEM_PIPE>){
    if($_ =~ m/^\[STEM\]: (.*)$/){
      $output .= $1;
      last;
    }
  }
  close STEM_PIPE;

  $stem_cache{$input} = $output;
  return $output;
}

