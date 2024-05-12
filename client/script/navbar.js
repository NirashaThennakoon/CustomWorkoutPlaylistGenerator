function logout() {
  // Perform any logout actions here (e.g., clearing session, logging out user, etc.)

  // Redirect the user to the login page
  window.location.href = "login.html";
}
document
  .getElementById("logoutLink")
  .addEventListener("click", function (event) {
    event.preventDefault();
    logout();
  });
