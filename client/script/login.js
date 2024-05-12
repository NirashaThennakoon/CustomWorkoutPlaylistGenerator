document.getElementById("login-form").addEventListener("submit", function (e) {
  const baseURL = config.baseUrl;
  e.preventDefault();

  var email = document.getElementById("email").value;
  var password = document.getElementById("password").value;

  // // Basic email validation
  // if (!isValidEmail(email)) {
  //   document.getElementById('message').textContent = "Please enter a valid email address.";
  //   return;
  // }

  var formData = {
    email: email,
    password: password,
  };

  fetch(baseURL + "/api/user/" + email, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(formData),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then((data) => {
      // Assuming server returns user role
      console.log(data);
      if (data.user_type === "admin") {
        // Redirect to admin dashboard
        window.location.href = "workouts.html";
      } else {
        // Handle successful login for other users
        console.log(data);
        document.getElementById("message").textContent = "Login successful!";
      }
    })
    .catch((error) => {
      // Handle login error
      console.error("There was a problem with the login:", error);
      document.getElementById("message").textContent =
        "Login failed. Please try again.";
    });
});
