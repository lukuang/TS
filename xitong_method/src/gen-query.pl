#!/usr/bin/env perl

#
# generate the query list for robust 04
#

use strict;
use Getopt::Long;

my $script_name = "gen-query.pl";
my $usage = "$script_name [-v] <raw>\n";

my $verbose = 0;
GetOptions('verbose!' => \$verbose,
  ) or die $usage;

my $raw_file = shift or die $usage;

my $ent_file = "query/ent";
my $sgml_file = "query/sgml";
my $desc_file = "query/desc";
my $indri_file = "query/indri";

my $stoplist_file = "data/stoplist";

my %query_list;

main();

sub main(){
  parse_raw();
  save_ent();
  save_sgml();
  save_indri();
  save_desc_ns();
}

sub parse_raw(){
  open RAW, $raw_file or die "Can't open `$raw_file': $!\n";
  print "Loading $raw_file\n";

  my $qid = 0;
  my $is_in_desc = 0;
  my $title = "";
  my $query = "";

  while(<RAW>){
    chomp;
    next if /^$/;

    next if /<event>/;
    next if /<\/event>/;

    if(m/<id>(\d+)/){
      $qid = $1;
      print "qid is $qid\n";
      next;
    }

    if(m/<title>([^<]+)/){
      $title .= " ".$1;
      next;
    }
    if(m/<query>([^<]+)/){
      $title .= " ".$1;
      next;
    }
    
    if(m/<end>/){
      $is_in_desc = 1;
      next;
    }

    if(1 == $is_in_desc){
      # we have reached the end of the desc field
      if(/<type>/){
        # save it
        $query_list{$qid}{title} = $title;
        print "title is $title\n";
        $query_list{$qid}{query} = $query;
        $title = "";
        $query = "";
        $is_in_desc = 0;
        next;
      }
      $query = "$query $_";
      next;
    }
  }

  close RAW;
}

sub save_ent(){
  open ENT, ">" . $ent_file or die "Can't open `$ent_file': $!\n";
  print "Saving $ent_file\n";

  for my $qid(sort {$a<=>$b} keys %query_list){
    my $ent = $query_list{$qid}{title};

    print ENT "$qid : $ent\n";
  }

  close ENT;
}

sub save_sgml(){
  open SGML, ">" . $sgml_file or die "Can't open `$sgml_file': $!\n";
  print "Saving $sgml_file\n";

  for my $qid(sort {$a<=>$b} keys %query_list){
    #my $query = $query_list{$qid}{query};
    my $query = $query_list{$qid}{title};

    print SGML "<DOC>\n";
    print SGML "<DOCNO> $qid <\/DOCNO>\n";
    print SGML "$query\n";
    print SGML "<\/DOC>\n";
  }

  close SGML;
}

sub save_indri(){
  open INDRI, ">" . $indri_file or die "Can't open `$indri_file': $!\n";
  print "Saving $indri_file\n";
  print INDRI "<parameters>\n";

  for my $qid(sort {$a<=>$b} keys %query_list){
    #my $query = $query_list{$qid}{query};
    my $query = $query_list{$qid}{title};
    $query = trim($query);

    print INDRI "\t<query>\n";
    print INDRI "\t<trecFormat>true</trecFormat>\n";
    print INDRI "\t\t<number>$qid<\/number>\n";
    print INDRI "\t\t<text>$query<\/text>\n";
    print INDRI "\t<\/query>\n";
  }
 
  print INDRI "\t<count>2000<\/count>\n";
  print INDRI "<\/parameters>\n";

  close INDRI;
}

# save the description fields without stop words
sub save_desc_ns(){
  my %stop_list;
  open STOPLIST, $stoplist_file or die "can not open `$stoplist_file': $!\n";
  while(<STOPLIST>){
    chomp;
    next if /^$/;
    $stop_list{$_} = 1;
  }
  close STOPLIST;

  my %desc_list;

  for my $qid(sort {$a<=>$b} keys %query_list){
    my $query = $query_list{$qid}{title};

    #$query = trim($query);
    my $desc_query = "";
    my @term_array = split / /, $query;
    for my $term(@term_array){
      #eliminate the stop words
      next if defined $stop_list{$term};
      $desc_query = "$desc_query $term";
    }
    $desc_query = trim($desc_query);
    #$desc_list{$qid} = $desc_query;
    $desc_list{$qid} = $query;
  }
  
  open DESC, ">" . $desc_file or die "Can't open `$desc_file': $!\n";
  print "Saving $desc_file\n";

  for my $qid(sort {$a<=>$b} keys %desc_list){
    my $desc_query = $desc_list{$qid};
    print DESC "$qid:$desc_query\n";
  }

  close DESC;
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

  return $str;
}

