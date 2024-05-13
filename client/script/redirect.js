window.onload = function () {
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function () {
    if (this.readyState == 4) {
      if (this.status == 404) {
        // Page not found, redirect to 404 page

        window.location.href = "../html/404.html";
        console.log("Sending XMLHttpRequest to: " + window.location.href);
      }
    }
  };
  xhttp.open("GET", window.location.href, true);
  xhttp.send();
};
