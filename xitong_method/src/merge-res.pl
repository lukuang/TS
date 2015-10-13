#!/usr/bin/env perl

#
# combine the results of robust04 for the first 100 queries and the remain
# 150 queries
#
# Version: 1.0.
#

use strict;
use POSIX;
use Getopt::Long;

my $usage = "merge-res.pl [-v] <dir-100> <dir-150> <dir-all>\n";
my $verbose = 0;
my $rp = 0;

GetOptions('verbose!' => \$verbose,
    ) or die $usage;

my $dir_100 = shift or die $usage;
my $dir_150 = shift or die $usage;
my $dir_all = shift or die $usage;

# main routine

main();

sub main(){
  do_merge();
}

sub do_merge(){
  # open the dir_100 directory
  opendir(my $dh_100, $dir_100) or die "Can't opendir `$dir_100': $!\n";
  my @files_100 = grep { !/^\./ && -f "$dir_100/$_" } readdir($dh_100);
  closedir $dh_100;
  print @files_100 . " files in total in $dir_100\n";

  # open the dir_150 directory
  opendir(my $dh_150, $dir_150) or die "Can't opendir `$dir_150': $!\n";
  my @files_150 = grep { !/^\./ && -f "$dir_150/$_" } readdir($dh_150);
  closedir $dh_150;
  print @files_150 . " files in total in $dir_150\n";

  my %hash_100 = map { $_ => 1 } @files_100;
  my %shared;

  for my $file(@files_150){
    if(defined $hash_100{$file}){
      $shared{$file} = 1;
    }
  }

  my $num = scalar keys %shared;
  print "$num shared files between $dir_100 and $dir_150\n";

  for my $file(sort {$a cmp $b} keys %shared){
    my $file_100 = "$dir_100/$file";
    my $file_150 = "$dir_150/$file";

    unless(-e $file_100){
      print "$file_100 does not exist!\n";
      next;
    }

    unless(-e $file_150){
      print "$file_150 does not exist!\n";
      next;
    }

    my $file_all = "$dir_all/$file";
    my $cmd = "cat $file_100 $file_150 > $file_all";
    print "Executing: $cmd\n" if $verbose;
    system($cmd);
    print "merging into $file_all\n";
  }
}

