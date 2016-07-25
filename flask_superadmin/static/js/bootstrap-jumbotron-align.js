window.onload = function() {
  realignJumbotron();
}

window.onresize = function() {
  realignJumbotron();
}

function realignJumbotron() {
  jumbo.style.marginTop = (window.innerHeight - jumbo.offsetHeight) / 2 + 'px';
}
