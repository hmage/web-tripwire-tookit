#!/usr/bin/perl

# Web Tripwire ----------------------------------------
#  Charles Reis, University of Washington, 2007.
#
# This script outputs JavaScript code that can detect whether
# a page has been modified between leaving the server and
# arriving in the browser (e.g., by an ISP that injects ads).
#
# The script can be run offline to generate a static JavaScript
# file, as follows:
#   webtripwire.cgi "page=foo.html" > foo-webtripwire.js
# (In this case, the first two lines of the resulting file must
# must be deleted.)
#
# Alternatively, it can be run online to generate JavaScript
# web tripwires on the fly.  Simply reference it from a script tag:
#   <script src="webtripwire.cgi?page=foo.html"></script>
#
# To prevent abuse, the "page" parameter to the script can only
# be set to values that are contained in the @validPages array.

use strict;
use CGI;
use URI::Escape;

# -------------- Configuration ------------------

my @validPages = (
  # LIST VALID FILENAMES HERE
  "index.html"
);

# Whether to enable demo mode.  Here, "*-mod.html" is checked
# against "*.html", to artificially trigger the web tripwire.
# See the "sample-cgi" directory for an example.
# 
my $demoMode = 0;

# Name of the CGI file to request when a change is detected.
my $submitCGIFilename = "webtripwire-submit.cgi";

# -----------------------------------------------

# Determine "page" parameter
my $cgi = new CGI;
print $cgi->header();
my $page = $cgi->param('page');

# Check to make sure this is a valid page
my $allowPage = 0;
foreach my $validPage (@validPages) {
  if ($page eq $validPage) {
    $allowPage = 1;
  }
}
if (!$allowPage) {
  exit;
}


my $html;
if ($demoMode) {
  # Remove the "-mod" portion of the filename for the demo.
  #  This way, the modified page is compared against the
  #  unmodified page, and a change is reported.
  my $compareAgainst = $page;
  $compareAgainst =~ s/-mod//;
  open(HTMLFILE, $compareAgainst) or die ("Couldn't open file.");
}
else {
  open(HTMLFILE, $page) or die ("Couldn't open file.");
}

# Read the page contents to generate the known-good representation.
while (my $line = <HTMLFILE>) {
  $html .= $line;
}
close(HTMLFILE);

# Escape the page contents with the same algorithm as JavaScript's
#  encodeURI function.
$html = uri_escape($html, "^A-Za-z0-9\-_.!~*'();,/?:\@\\\$&=+#");

# Output the JavaScript file containing the web tripwire code.
print <<END_HTML;
/* Client-side web tripwire script to detect page modifications.
 * Charles Reis, University of Washington, 2007.
 */

WebTripwire = new Object();

// URL of the page to test:
WebTripwire.targetPageURL = "$page";

// HTML of the page to test, as an encodedURI:
WebTripwire.encodedTargetPageHTML = "$html";

// URL of the page to notify, in the event of a detected change:
WebTripwire.notifyChangeURL = "$submitCGIFilename";

/* Fetches the target page with an XmlHttpRequest and compares it to the
 * expected HTML string.  If they differ, report the modified HTML to
 * the server and optionally the user.
 * The callback argument is invoked if a change is detected.
 */
WebTripwire.detect = function(callback) {
  var req = WebTripwire.newXHR();
  
  // Create a handler for the test page request
  var handler = function() {
    // Check if the request state is loaded and OK
    if (req.readyState == 4 && req.status == 200) {
    
      // See if the actual HTML is the same as the expected HTML.
      var targetPageHTML = decodeURI(WebTripwire.encodedTargetPageHTML);
      if (req.responseText != targetPageHTML) {
        // Detected modification
        //alert(encodeURI(req.responseText));  // for debugging
        
        // Notify server
        if (WebTripwire.notifyChangeURL) {
          var notify = WebTripwire.newXHR();
          
          // Create a handler for the notification request
          var notifyHandler = function() {
            if (notify.readyState == 4 && notify.status == 200) {
              // Notify the user
              WebTripwire.react(targetPageHTML, req.responseText, notify.responseText);
            }
          };
          
          // Create a results string to send back
          var results;
          results = "actualHTML=" + encodeURIComponent(req.responseText);
          notify.onreadystatechange = notifyHandler;
          notify.open("POST", WebTripwire.notifyChangeURL, true);
          notify.setRequestHeader("Content-Type", 
            "application/x-www-form-urlencoded");
          notify.send(results);
        }
        
        // Invoke the callback
        if (callback && typeof callback == 'function') {
          callback(req.responseText);
        }
        
      }
    }
  };
  
  // Make an asynchronous request for the test page
  req.onreadystatechange = handler;
  req.open("GET", WebTripwire.targetPageURL, true);
  req.send(null);
};

/* Function to display a message to the user when a change is detected.
 */
WebTripwire.react = function(expected, actual, message) {
  if (message == null) {
    // Don't print anything
    return;
  }
  // Escape angle brackets for printing HTML source code
  expected = expected.replace(/</g, '&lt;').replace(/>/g, '&gt;');
  actual = actual.replace(/</g, '&lt;').replace(/>/g, '&gt;');
  var insObj = { text:"" };
  var diff = jsd_diffString(expected, actual, insObj);
  diff = diff.replace(/\\n/g, "<br>\\n").replace(/"/g, "&quot;");
  
  WebTripwire.diff = "<html><body>\\n" + message +
    "<hr>\\n" + diff + "\\n</body></html>";
    
  // Create a div for a message to the user
  var messagebar = document.createElement('div');
  messagebar.id = "webtripwirebar";
  document.body.insertBefore(messagebar, document.body.firstChild);
  
  // Display a message to the user
  var infobar = new informationbar();
  infobar.setContent('We have detected that this page has been modified in flight.  For more information, click <a onclick="javascript:w=window.open();w.document.write(WebTripwire.diff);w.document.close()"><u>here</u></a>.')
  //infobar.setfrequency('session');  // make the bar appear once per session
  infobar.initialize();

}

/* Copied cross-browser code for getting an XMLHttpRequest object.
 * Source: http://www.hackorama.com/ajax/
 */
WebTripwire.newXHR = function() {
  var xmlreq = false;
  if (window.XMLHttpRequest) {
    xmlreq = new XMLHttpRequest();
  } else if (window.ActiveXObject) {
    // Try ActiveX
    try { 
      xmlreq = new ActiveXObject("Msxml2.XMLHTTP");
    } catch (e1) { 
      // first method failed 
      try {
        xmlreq = new ActiveXObject("Microsoft.XMLHTTP");
      } catch (e2) {
        // both methods failed 
      } 
    }
  }
  return xmlreq;
};


/* Add stylesheet for tripwire bar. */
WebTripwire.css = document.createElement('link');
WebTripwire.css.rel = "StyleSheet";
WebTripwire.css.href = "webtripwire.css";
WebTripwire.css.type = "text/css";
document.getElementsByTagName("head")[0].appendChild(WebTripwire.css);

/* Add an onload handler to run the tripwire. 
 * Credit: http://simonwillison.net/2004/May/26/addLoadEvent/
 */
WebTripwire.addLoadEvent = function(newonload) {
  var oldonload = window.onload;
  if (typeof window.onload != 'function') {
    window.onload = newonload;
  } else {
    window.onload = function() {
      if (oldonload) {
        oldonload();
      }
      newonload();
    }
  }
}
WebTripwire.addLoadEvent(WebTripwire.detect);

/*
 * Javascript Diff Algorithm
 *  By John Resig (http://ejohn.org/)
 *  Modified by Chu Alan "sprite"
 *  Modified by Charles Reis
 *
 * More Info:
 *  http://ejohn.org/projects/javascript-diff-algorithm/
 */

function jsd_escape(s) {
    var n = s;
    //n = n.replace(/&/g, "&amp;");
    n = n.replace(/</g, "&lt;");
    n = n.replace(/>/g, "&gt;");
    n = n.replace(/"/g, "&quot;");

    return n;
}

function jsd_diffString( o, n, insObj ) {
  o = o.replace(/\\s+\$/, '');
  n = n.replace(/\\s+\$/, '');
  if (insObj == null) insObj = new Object();

  var out = jsd_diff(o == "" ? [] : o.split(/\\s+/), n == "" ? [] : n.split(/\\s+/) );
  var str = "";

  var oSpace = o.match(/\\s+/g);
  if (oSpace == null) {
    oSpace = ["\\n"];
  } else {
    oSpace.push("\\n");
  }
  var nSpace = n.match(/\\s+/g);
  if (nSpace == null) {
    nSpace = ["\\n"];
  } else {
    nSpace.push("\\n");
  }

  if (out.n.length == 0) {
      for (var i = 0; i < out.o.length; i++) {
        str += "<del style='background:#FFE6E6;'>" + jsd_escape(out.o[i]) + oSpace[i] + "</del>";
      }
  } else {
    if (out.n[0].text == null) {
      for (n = 0; n < out.o.length && out.o[n].text == null; n++) {
        str += "<del style='background:#FFE6E6;'>" + jsd_escape(out.o[n]) + oSpace[n] + "</del>";
      }
    }

    for ( var i = 0; i < out.n.length; i++ ) {
      if (out.n[i].text == null) {
        str += "<ins style='background:#E6FFE6;'>" + jsd_escape(out.n[i]) + nSpace[i] + "</ins>";
        insObj.text += jsd_escape(out.n[i]) + nSpace[i];
      } else {
        var pre = "";

        for (n = out.n[i].row + 1; n < out.o.length && out.o[n].text == null; n++ ) {
          pre += "<del style='background:#FFE6E6;'>" + jsd_escape(out.o[n]) + oSpace[n] + "</del>";
        }
        str += " " + out.n[i].text + nSpace[i] + pre;
      }
    }
  }
  
  return str;
}

function jsd_diff( o, n ) {
  var ns = new Object();
  var os = new Object();
  
  for ( var i = 0; i < n.length; i++ ) {
    if ( ns[ n[i] ] == null )
      ns[ n[i] ] = { rows: new Array(), o: null };
    ns[ n[i] ].rows.push( i );
  }
  
  for ( var i = 0; i < o.length; i++ ) {
    if ( os[ o[i] ] == null )
      os[ o[i] ] = { rows: new Array(), n: null };
    os[ o[i] ].rows.push( i );
  }
  
  for ( var i in ns ) {
    if ( ns[i].rows.length == 1 && typeof(os[i]) != "undefined" && os[i].rows.length == 1 ) {
      n[ ns[i].rows[0] ] = { text: n[ ns[i].rows[0] ], row: os[i].rows[0] };
      o[ os[i].rows[0] ] = { text: o[ os[i].rows[0] ], row: ns[i].rows[0] };
    }
  }
  
  for ( var i = 0; i < n.length - 1; i++ ) {
    if ( n[i].text != null && n[i+1].text == null && n[i].row + 1 < o.length && o[ n[i].row + 1 ].text == null && 
         n[i+1] == o[ n[i].row + 1 ] ) {
      n[i+1] = { text: n[i+1], row: n[i].row + 1 };
      o[n[i].row+1] = { text: o[n[i].row+1], row: i + 1 };
    }
  }
  
  for ( var i = n.length - 1; i > 0; i-- ) {
    if ( n[i].text != null && n[i-1].text == null && n[i].row > 0 && o[ n[i].row - 1 ].text == null && 
         n[i-1] == o[ n[i].row - 1 ] ) {
      n[i-1] = { text: n[i-1], row: n[i].row - 1 };
      o[n[i].row-1] = { text: o[n[i].row-1], row: i - 1 };
    }
  }
  
  return { o: o, n: n };
}


/***********************************************

* Animated Information Bar- by JavaScript Kit (www.javascriptkit.com)
* This notice must stay intact for usage
* Visit JavaScript Kit at http://www.javascriptkit.com/ for this script and 100s more

***********************************************/

function informationbar(){
        this.displayfreq="always"
        this.content='<a href="javascript:informationbar.close()"><img src="webtripwire-close.gif" style="width: 14px; height: 14px; float: right; border: 0; margin-right: 5px" /></a>'
}

informationbar.prototype.setContent=function(data){
        this.content=this.content+data
        document.getElementById("webtripwirebar").innerHTML = this.content;
}

informationbar.prototype.animatetoview=function(){
        var barinstance=this
        if (parseInt(this.barref.style.top)<0){
                this.barref.style.top=parseInt(this.barref.style.top)+5+"px"
                setTimeout(function(){barinstance.animatetoview()}, 50)
        }
        else{
                if (document.all && !window.XMLHttpRequest)
                this.barref.style.setExpression("top", 'document.compatMode=="CSS1Compat"? document.documentElement.scrollTop+"px" : body.scrollTop+"px"')
        else
                this.barref.style.top=0
        }
}

informationbar.close=function(){
        document.getElementById("webtripwirebar").style.display="none"
        if (this.displayfreq=="session")
                document.cookie="infobarshown=1;path=/"
}

informationbar.prototype.setfrequency=function(type){
        this.displayfreq=type
}

informationbar.prototype.initialize=function(){
        if (this.displayfreq=="session" && document.cookie.indexOf("infobarshown")==-1 || this.displayfreq=="always"){
                this.barref=document.getElementById("webtripwirebar")
                this.barheight=parseInt(this.barref.offsetHeight)
                this.barref.style.top=this.barheight*(-1)+"px"
                this.animatetoview()
        }
}

window.onunload=function(){
        this.barref=null
}

END_HTML
