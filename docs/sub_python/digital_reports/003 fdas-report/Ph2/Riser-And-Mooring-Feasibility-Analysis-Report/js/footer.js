
if (window.addEventListener) {              
  window.addEventListener("resize", browserResize);
} else if (window.attachEvent) {                 
  window.attachEvent("onresize", browserResize);
}
var xbeforeResize = window.innerWidth;
var ybeforeResize = window.innerWidth;
var zbeforeResize = window.innerWidth;
var sbeforeResize = window.innerWidth;
function skyscraperResize() {
if (window.innerWidth < 975 + 17 && document.getElementById("div-gpt-ad-1422003450156-5")) {
  document.getElementById("div-gpt-ad-1422003450156-5").style.minHeight="0";
  }
}
function browserResize() {
  var afterResize = window.innerWidth;
  if ((xbeforeResize < (1450 + 14) && afterResize >= (1450 + 14)) || (xbeforeResize >= (1450 + 14) && afterResize < (1450 + 14)) ||
    (xbeforeResize < (700 + 14) && afterResize >= (700 + 14)) || (xbeforeResize >= (700 + 14) && afterResize < (700 + 14)) ||
    (xbeforeResize < (480 + 17) && afterResize >= (480 + 17)) ||(xbeforeResize >= (480 + 17) && afterResize < (480 + 17))) {
    xbeforeResize = afterResize;
    googletag.cmd.push(function() {
      googletag.pubads().refresh([gptAdSlots[0]]);
    });
  }
  if ((ybeforeResize < (1675 + 14) && afterResize >= (1675 + 14)) || (ybeforeResize >= (1675 + 14) && afterResize < (1675 + 14)) ||
    (ybeforeResize < (1100 + 14) && afterResize >= (1100 + 14)) || (ybeforeResize >= (1100 + 14) && afterResize < (1100 + 14)) ||
    (ybeforeResize < (975 + 17) && afterResize >= (975 + 17)) || (ybeforeResize >= (975 + 17) && afterResize < (975 + 17))) {
    ybeforeResize = afterResize;
      skyscraperResize()
    googletag.cmd.push(function() {
      googletag.pubads().refresh([gptAdSlots[1]]);
    });
  }
  if ((zbeforeResize < (1240 + 14) && afterResize >= (1240 + 14)) || (zbeforeResize >= (1240 + 14) && afterResize < (1240 + 14))) {
    zbeforeResize = afterResize;
    googletag.cmd.push(function() {
      googletag.pubads().refresh([gptAdSlots[2], gptAdSlots[3]]);
    });
  }
  if ((sbeforeResize < (1675 + 14) && afterResize >= (1675 + 14)) || (sbeforeResize >= (1675 + 14) && afterResize < (1675 + 14)) ||
    (sbeforeResize < (1100 + 14) && afterResize >= (1100 + 14)) || (sbeforeResize >= (1100 + 14) && afterResize < (1100 + 14)) ||
    (sbeforeResize < (975 + 17) && afterResize >= (975 + 17)) || (sbeforeResize >= (975 + 17) && afterResize < (975 + 17))) {
    sbeforeResize = afterResize;
    googletag.cmd.push(function() {
      googletag.pubads().refresh([gptAdSlots[4]]);
    });
  }
}
skyscraperResize();
function open_menu() {
  var x, m;
  m = (document.getElementById("leftmenu") || document.getElementById("sidenav"));
  if (m.style.display == "block") {
    close_menu();
  } else {
    w3_close_all_nav();  
    m.style.display = "block";
    if (document.getElementsByClassName) {
      x = document.getElementsByClassName("chapter")
      for (i = 0; i < x.length; i++) {
        x[i].style.visibility = "hidden";
      }
      x = document.getElementsByClassName("nav")
      for (i = 0; i < x.length; i++) {
        x[i].style.visibility = "hidden";
      }
      x = document.getElementsByClassName("sharethis")
      for (i = 0; i < x.length; i++) {
        x[i].style.visibility = "hidden";
      }
    }
    fix_sidemenu();
  }
}

function close_menu() {
  var m;
  m = (document.getElementById('leftmenu') || document.getElementById('sidenav'));
  m.style.display = 'none';  
  if (document.getElementsByClassName) {
    x = document.getElementsByClassName('chapter')
    for (i = 0; i < x.length; i++) {
      x[i].style.visibility = 'visible';
    }
    x = document.getElementsByClassName('nav')
    for (i = 0; i < x.length; i++) {
      x[i].style.visibility = 'visible';
    }
    x = document.getElementsByClassName('sharethis')
    for (i = 0; i < x.length; i++) {
      x[i].style.visibility = 'visible';
    }            
  }
}
