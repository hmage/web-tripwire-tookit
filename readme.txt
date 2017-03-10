Web Tripwire Toolkit ------------------------------
  
  Charles Reis, University of Washington, 2007.
  Version 0.5, January 14, 2008.


The files in this package can be used to add a "web tripwire" to a web
page, to detect any changes made to the page between the server and
the client's browser.  Web tripwires use JavaScript code to detect
textual changes to a page's HTML source code, and they can report any
changes to the server and the user.

Web tripwires consist of JavaScript, CSS, and HTML code that should be
compatible with most modern browsers, including Firefox, Internet
Explorer, Safari, Opera, and Konqueror.


Requirements -----

In this version of the toolkit, you will need to be able to run Perl
CGI scripts on your web server, because the web tripwire connects to
a CGI script to help identify detected changes.

Future versions will make this an optional requirement.


Usage -----

You can add a web tripwire to any static page as shown below.

1) Place the webtripwire.cgi and webtripwire-submit.cgi files in the
same directory as the page you want to instrument.  Configure the variables
at the top of each script as desired.  At a minimum, you must define the
"validPages" array in webtripwire.cgi.

2) Place webtripwire.css and webtripwire-close.gif in the same directory.

3) Add the following line within the <head> tag of your page.  Replace
"PAGEURL" with the name of your page.

  <script type="text/javascript" src="webtripwire.cgi?page=PAGEURL"></script>
  
That's it!  An example is provided in the "sample-cgi" directory.


Alternative Usage -----

You can also pre-compute the web tripwire for a given page, rather than
invoking a CGI script on every page request.  After configuring the
webtripwire.cgi script, run it from a command line as follows (replacing
PAGEURL with the name of your page):

./webtripwire.cgi "page=PAGEURL" > webtripwire-PAGEURL.js

You will need to edit the webtripwire-PAGEURL.js file and remove the first
two lines.  Then follow steps 2 and 3 in the instructions above, but replace
"webtripwire.cgi?page=PAGEURL" with "webtripwire-PAGEURL.js".

An example of this approach is provided in the "sample" directory.


About Web Tripwires -----

Web tripwires were designed as part of a research project by Charlie Reis,
Steve Gribble, Yoshi Kohno, and Nick Weaver, at the University of Washington
and ICSI.  More information can be found online at the URL below.

http://www.cs.washington.edu/research/security/web-tripwire.html
