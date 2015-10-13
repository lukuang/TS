#!/usr/local/bin/perl
# !/usr/bin/env perl

#
# Description: rank the entities using relationships from the 
# unstructured data
# 
#

use strict;
use lib '/usa/xliu/usr/lib/site_perl/5.8.8/';
use Getopt::Long;
use String::CamelCase qw(decamelize wordsplit);

my $script_name = "ent-doc-rank.pl";
my $usage = "$script_name [-v]\n";

my $qent_match_dbpedia_file = "data/query-ent-dbpedia.map";
my $query_desc_file = "query/desc";
#my $query_desc_file = "query/ent";
my $query_ent_map_file = "data/query-ent-doc.map";

my $raw_file = "corpus/top.2000";
my $stop_list_file = "data/stoplist";
my $idf_hash_file = "corpus/idf.hash.2000";

my $doc_dbpedia_map_in_file = "data/doc-dbpedia-map/in";
my $doc_dbpedia_map_out_file = "data/doc-dbpedia-map/out";
my $ent_link_graph_in_file = "data/in.ent.list";
my $ent_link_graph_out_file = "data/out.ent.list";

my $save_rank_file = "res/ent/text.txt";
#my $save_rank_file = "res/ent/ent.txt";

my %qent_dbent_list;
my %qent_dbpedia_list;
my %db_qent_list;
my %query_desc_list;
my %qent_doc_map;
my %doc_qent_map;

my %doc_list;
my %idf_hash;

my %ent_list;
my %ent_rev_list;
my %e2d_map;
my %link_graph;

my %ent_cand_list;
my %rank_list;
my %rank_idf_list;

my %stop_list;

my $VOB_TOTAL = 1;
my $DOC_TOTAL = 1;

my $verbose = 0;
GetOptions('verbose!' => \$verbose,
  ) or die $usage;

main();

sub main(){
  load_qent_match_dbpedia();
  load_query_desc();
  load_query_ent_map();

  load_raw();
  load_idf_hash();
  load_stop_list();

  load_e2d_map($doc_dbpedia_map_in_file);
  load_e2d_map($doc_dbpedia_map_out_file);
  load_ent_link_graph($ent_link_graph_in_file);
  load_ent_link_graph($ent_link_graph_out_file);

  do_rank();

  do_save();
}

sub load_qent_match_dbpedia(){
  open FILE, $qent_match_dbpedia_file 
    or die "Can't open `$qent_match_dbpedia_file': $!\n";
  print "Loading $qent_match_dbpedia_file\n";

  while(<FILE>){
    chomp;
    next if /^$/;

    my ($qid, $qent, $uri) = split / : /;
    next if !defined $qid;
    $qent = trim($qent);
    $uri = lc $uri;
    $qent_dbpedia_list{$qid}{$qent} = $uri;
    $db_qent_list{$qid}{$uri}{QENT} = $qent;

    # process the DBPedia URI
    my $db_ent = $uri;
    if($uri =~ m|http://dbpedia.org/resource/(.*)|){
      $db_ent = $1;
      $db_ent = decamelize($db_ent);
      $db_ent = trim($db_ent);
    }
    $qent_dbent_list{$qid}{$db_ent} = $uri;
    $db_qent_list{$qid}{$uri}{DB_ENT} = $db_ent;
  }

  close FILE;
}

sub load_query_desc(){
  open DESC, $query_desc_file 
    or die "Can not open `$query_desc_file': $!\n";
  print "Loading $query_desc_file\n";

  while(<DESC>){
    chomp;
    next if /^$/;

    my ($qid, $query) = split /:/;
    $qid = trim($qid);
    $query = trim($query);
    $query_desc_list{$qid} = $query;
  }

  close DESC;
}

sub load_query_ent_map(){
  open MAP, $query_ent_map_file or die "Can't open `$query_ent_map_file': $!\n";
  print "Loading $query_ent_map_file\n";

  while(<MAP>){
    chomp;
    next if /^$/;

    my ($qid, $did, $type, $ent) = split /--/;

    if("WIKI" eq $type){
      if(defined $qent_dbent_list{$qid}{$ent}){
        my $uri = $qent_dbent_list{$qid}{$ent};
        $qent_doc_map{$qid}{$did} = $uri;
      }
    }else{
      if(defined $qent_dbpedia_list{$qid}{$ent}){
        my $uri = $qent_dbpedia_list{$qid}{$ent};
        $qent_doc_map{$qid}{$did} = $uri;
      }
    }
    unless(defined $qent_doc_map{$qid}{$did}){
      print "Unresolved query-ent: $qid-$ent-$did\n";
    }
  }

  close MAP;
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

        $doc = trim($doc);
        $doc = " $doc ";
        $doc_list{$did} = $doc;
        ++$DOC_TOTAL;

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

sub load_idf_hash(){
  open HASH, $idf_hash_file 
    or die "Can not open `$idf_hash_file': $!\n";
  print "Loading $idf_hash_file\n";

  while(<HASH>){
    chomp;
    next if /^$/;

    my ($term, $did, $cnt) = split;
    $idf_hash{$term}{$did} = $cnt;
    $VOB_TOTAL += $cnt;
  }

  close HASH;
}

sub load_stop_list(){
  open STOP_LIST, $stop_list_file 
    or die "Can't open `$stop_list_file': $!\n";
  print "Loading $stop_list_file ...\n";

  while (<STOP_LIST>) {
    chomp;
    next if /^$/;

    $stop_list{$_} = 1;
  }

  close STOP_LIST;
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
    $uri = lc $uri;
    $ent_list{$uri} = $ent;
    $ent_rev_list{$ent} = $uri;
    $e2d_map{$uri}{$did} = 1;
  }

  close MAP;
}

sub load_ent_link_graph(){
  my $usage = "Usage: load_ent_link_graph(\$graph_file)\n";
  my $graph_file = shift or die $usage;

  open GRAPH, $graph_file or die "Can not open `$graph_file': $!\n";
  print "Lading $graph_file\n";

  while(<GRAPH>){
    chomp;
    next if /^$/;

    my($from, $to) = split / : /;
    $from = lc $from;
    $to = lc $to;
    $link_graph{$from}{$to} = 1;
  }

  close GRAPH;
}

sub do_rank(){
  # first, generate entity candidate list for each query
  print "Generating entity candidate list\n";
  for my $qid(sort {$a<=>$b} keys %qent_dbpedia_list){

    # for debug purpose only
    #next unless 308 == $qid;

    for my $qent(keys %{$qent_dbpedia_list{$qid}}){
      my $quri = $qent_dbpedia_list{$qid}{$qent};
      for my $to_uri(keys %{$link_graph{$quri}}){
        $ent_cand_list{$qid}{$quri}{$to_uri} = 1;
      }
    }
  }

  # rank the entity candidates then
  for my $qid(sort {$a<=>$b} keys %ent_cand_list){
    print "Topic $qid\n";

    for my $quri(sort {$a cmp $b} keys %{$ent_cand_list{$qid}}){
      my $qent = $db_qent_list{$qid}{$quri}{QENT};
      my $db_ent = $db_qent_list{$qid}{$quri}{DB_ENT};
      my $qent_idf = calc_ent_idf($qent);
      my $db_ent_idf = calc_ent_idf($db_ent);
      my $max_ent_idf = $qent_idf;
      $max_ent_idf = $db_ent_idf if $max_ent_idf < $db_ent_idf;

      for my $ent_uri(sort {$a cmp $b} keys %{$ent_cand_list{$qid}{$quri}}){

        # for debug purpose only
        #next unless "http://dbpedia.org/resource/Animal" eq $ent_uri;

        my $sim = calc_sim($qid, $quri, $ent_uri);
        if(defined $rank_list{$qid}{$ent_uri}){
          $rank_list{$qid}{$ent_uri} += $sim;
        }else{
          $rank_list{$qid}{$ent_uri} = $sim;
        }

        # keep the IDF records of entity candidates
        if(defined $rank_idf_list{$qid}{$ent_uri}){
          if($rank_idf_list{$qid}{$ent_uri} < $max_ent_idf){
            $rank_idf_list{$qid}{$ent_uri} = $max_ent_idf;
          }
        }else{
          $rank_idf_list{$qid}{$ent_uri} = $max_ent_idf;
        }

        #last;
      }
    }
    #last if $qid > 410;
  }
}

# calculate the IDF of an entity
sub calc_ent_idf(){
  my $usage = "calc_ent_idf(\$ent)\n";
  my $ent = shift;

  unless(defined $ent){
    print $usage;
    return 0;
  }

  my @terms = split / /, $ent;
  my $idf_sum = 0;
  for my $t(@terms){
    my $df = scalar keys %{$idf_hash{$t}};
    my $idf_t = log(($DOC_TOTAL + 1) / ($df + 0.5));
    $idf_sum += $idf_t;
  }

  my $len = scalar @terms;
  my $idf_ave = $idf_sum / $len;
  return $idf_ave;
}

# calculate the similarity between two entities 
sub calc_sim(){
  my $usage = "Usage: calc_sim(\$qid, \$quri, \$ent_uri)\n";
  my $qid = shift;
  my $quri = shift;
  my $ent_uri = shift;

  unless(defined $qid and defined $quri and defined $ent_uri){
    print $usage;
    return 0.0;
  }

  # generate the list of documents in which to documents co-occur
  my %ovp_docs;
  for my $did(keys %{$qent_doc_map{$qid}}){
    next if $quri != $qent_doc_map{$qid}{$did};

    if(defined $e2d_map{$ent_uri}{$did}){
      $ovp_docs{$did} = 1;
    }
  }

  my $sim = 0.0;
  my $query = $query_desc_list{$qid};
  # calculate the similarity score by enumerating all the co-occurred
  # documents
  for my $did(keys %ovp_docs){
    if(!defined $doc_list{$did}){
      print "I can not find document $did\n";
      next;
    }
    my $doc = $doc_list{$did};

    # for debug purpose only
    #if($did eq "LA120490-0083"){
    #print "DID: $did\n";
    #}

    my $doc_sim = score($query, $did, $doc);
    $sim += $doc_sim;
  }

  return $sim;
}

# extract the context from a given position in a document
sub extract_context(){
  my $usage = "Usage: extract_context(\$did, \$quri, \$ent)\n";

}

sub do_save(){
  open FILE, ">" . $save_rank_file
    or die "Can not open `$save_rank_file': $!\n";
  print "Saving $save_rank_file\n";

  for my $qid(sort {$a<=>$b} keys %rank_list){
    my $rank = 0;
    for my $uri(sort {$rank_list{$qid}{$b}<=>$rank_list{$qid}{$a}} 
      keys %{$rank_list{$qid}}){

      my $score = $rank_list{$qid}{$uri};
      next if 0 == $score;
      my $ent = $ent_list{$uri};
      my $ent_idf = $rank_idf_list{$qid}{$uri};

      print FILE "$qid : $rank : $ent : $score : $uri : $ent_idf\n";
      $rank++;
      last if $rank > 100;
    }
  }

  close FILE;
}

# calculate the relevance score between query and document
sub score(){
  my $usage = "Usage: score(\$qry, \$did, \$doc)\n";
  my $qry = shift;
  my $did = shift;
  my $doc = shift;
  
  unless(defined $qry and defined $doc and defined $did){
    print $usage;
    return 0.0;
  }
  
  #my $sim = tfidf_score($qry, $doc);
  my $sim = dirichlet_score($qry, $did, $doc);
  return $sim;
}

# using TF-IDF to esimate the relevance score
sub tfidf_score(){
  my $usage = "Usage: tfidf_score(\$strA, \$strB)\n";
  my $strA = shift;
  my $strB = shift;

  unless(defined $strA and defined $strB){
    print $usage;
    return 0.0;
  }

  my @termsA = split / /, $strA;
  my @termsB = split / /, $strB;

  my %hashA;
  for my $t(@termsA){
    next if defined $stop_list{$t};
    $hashA{$t}++;
  }

  my %ovp;
  for my $t(@termsB){
    next if defined $stop_list{$t};
    if(defined $hashA{$t}){
      $ovp{$t}++;
    }
  }

  my $sim = 0.0;

  for my $t(keys %ovp){
    my $tf = $ovp{$t};
    my $df = 0;
    if(defined $idf_hash{$t}){
      $df = scalar keys %{$idf_hash{$t}};
    }else{
      print "term [$t] not found in idf_hash!\n";
      next;
    }

    if(0 == $df){
      $df = 1;
    }
    my $idf = log($DOC_TOTAL / $df);
    $sim += $tf * $idf;
  }

  return $sim;
}

# estimate the relevance score based on Dirichlet Prior method
sub dirichlet_score(){
  my $usage = "Usage: dirichlet_score(\$qry, \$did, \$doc)\n";
  my $qry = shift;
  my $did = shift;
  my $doc = shift;

  unless(defined $qry and defined $doc){
    print $usage;
    return 0.0;
  }

  my $mu = 3000;
  my $NUM_TERMS = 246940442;

  my @termsQry = split / /, $qry;
  my @termsDoc = split / /, $doc;

  my %hashQry;
  for my $t(@termsQry){
    next if defined $stop_list{$t};
    # accumulating c(w,q)
    $hashQry{$t}++;
  }

  my %ovp;
  for my $t(@termsDoc){
    next if defined $stop_list{$t};
    if(defined $hashQry{$t}){
      # accumulating the c(w, d)
      $ovp{$t}++;
    }
  }

  my $ql = scalar @termsQry;
  my $dl = scalar @termsDoc;
  my $sim = 0.0;

  for my $t(keys %ovp){
    my $cwq = $hashQry{$t};
    my $cwd = $ovp{$t};

    # estimate p(w|C) using maximum likelihood estimation
    my $cnt_sum = 0;
    if(defined $idf_hash{$t}){
      for my $did2(keys %{$idf_hash{$t}}){
        my $cnt = $idf_hash{$t}{$did2};
        $cnt_sum += $cnt;
      }
    }else{
      print "term [$t] not found in idf_hash!\n";
      next;
    }
    if(0 == $cnt_sum){
      $cnt_sum = 1;
    }
    my $pwc = $cnt_sum / $NUM_TERMS;
    my $inc = 0;
    $inc += $cwq * log(1 + ($cwd / ($mu * $pwc)));
    $sim += $inc;
  }

  $sim += $ql * log($mu / ($dl + $mu));

  return $sim;
}

sub trim(){
  my $usage = "Usage: trim(\$str)\n";
  my $str = shift;

  if(!defined $str){
    print $usage;
    return "";
  }

  # _ to space
  $str =~ s/\_/ /g;

  # remove non-word characters
  $str =~ s/\W+/ /g;
  
  # multiple spaces to single
  $str =~ s/\s+/ /g;

  #remove leading spaces
  $str =~ s/^\s//;

  # remove trailing spaces
  $str =~ s/\s$//;

  # to lowercase
  $str = lc $str;

  return $str;
}

