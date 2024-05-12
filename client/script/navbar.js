function logout() {
  localStorage.removeItem("userId");
  window.location.href = "../login.html";
}
document
  .getElementById("logoutLink")
  .addEventListener("click", function (event) {
    event.preventDefault();
    logout();
  });
