#!/usr/bin/perl

# Web Tripwire ----------------------------------------
#  Charles Reis, University of Washington, 2007.
#
# This script is used by web tripwires to report page modifications
# to the server.  It also attempts to classify modifications to
# provide a useful message for the user.

use strict;
use CGI;

# -------------- Configuration ------------------

# Each possible cause should contain:
#  - A regular expression to identify the cause
#  - Whether to notify the user
#  - A message to display about the cause
my @possibleCauses= ();

push @possibleCauses,
  [ "faireagle", 1,
    "NebuAd, a company that contracts with ISPs to inject advertisements " .
    "into web pages.  If you object to this practice, contact your ISP." ];

push @possibleCauses,
  [ "Begin Ad Muncher", 1,
    "Ad Muncher, a program designed to block ads.  You can test this by " .
    "disabling Ad Muncher and revisiting the page, to see if this message goes " .
    "away.  If so, Ad Muncher is the cause, and you can safely re-enable it." ];
    
push @possibleCauses,
  [ "Begin Ad Muncher.* Original URL", 1,
    "<b>Warning:</b> This version of Ad Muncher is vulnerable " .
    "to cross-site scripting attacks.  Be sure to upgrade " .
    "to Ad Muncher v4.71 or newer as soon as possible." ];


# Whether to always or never notify users of modifications, regardless of
# the settings in possibleCauses.  (Disabling takes precedence.)
my $enableAllNotifications = 1;
my $disableAllNotifications = 0;

# Directory to save results.  Leave empty to disable logging.
#  (still porting this feature from our measurement study)
my $logDir = "";


# -----------------------------------------------

my $cgi = new CGI;
print $cgi->header();

my $actualHTML = $cgi->param("actualHTML");

# -------------- Optionally log report ------------------

if ($logDir ne "") {
  # TODO: Add log entry... (still porting from measurement study)
}

# -------------- Look for likely causes ------------------
my @likelyCauses = ();
my $willNotify = $enableAllNotifications;

foreach my $possibleCause (@possibleCauses) {
  my ($pattern, $notify, $msg) = @{$possibleCause};
  #print "Searching for $pattern...\n";
  
  if ($actualHTML =~ m/$pattern/) {
    push @likelyCauses, $msg;
    $willNotify = $willNotify || $notify;
  }
}

# -------------- Optionally Print Message ------------------
if ($disableAllNotifications || !$willNotify) {
  exit;
}

print <<END_HTML;
<h1>Page Modification Detected</h1>
We have detected that our web page was modified between leaving our server and
arriving in your browser.  There are many possible causes for such a modification,
ranging from the use of personal firewalls to Internet Service Providers that
that inject advertisements.
<p>
END_HTML

if ($#likelyCauses == -1) {
  print "In this case, we are not certain what the cause of the modification is.<p>";
}
else {
  print "In this case, we suspect that the modification was caused by one ";
  print "or more of the following:\n<ul>\n";
  foreach my $likelyCause (@likelyCauses) {
    print "<li>$likelyCause\n";
  }
  print "</ul>\n";
}

print <<END_HTML;
For your reference, the actual HTML your browser received is shown below,
with the modifications highlighted.
END_HTML
