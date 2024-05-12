document.getElementById('login-form').addEventListener('submit', function(e) {
  const baseURL = config.baseUrl;
  e.preventDefault();

  var email = document.getElementById('email').value;
  var password = document.getElementById('password').value;

  // Basic email validation
  // if (!isValidEmail(email)) {
  //   document.getElementById('message').textContent = "Please enter a valid email address.";
  //   return;
  // }

  var formData = {
    email: email,
    password: password
  };

  fetch(baseURL+'api/user/'+email, {
    mode: 'no-cors',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': '1baf9207-4e72-4de8-b30b-fbbbbef5',
    },
    body: JSON.stringify(formData)
  }).then(response => {
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    return response.json(); // Parse response body as JSON
  })
  .then(data => {
    console.log(data)
    var userId = data.user_id;
    var apiKey = data.apiKey;
    localStorage.setItem('userId', userId);
    localStorage.setItem('apiKey', apiKey);

    if (data.user_type === 'admin') {
      // Redirect to admin dashboard
      window.location.href = 'adminDashboard.html';
    } else {
      // Handle successful login for other users
      window.location.href = 'regularUser/workoutplans.html';
    }
  })
  .then((data) => {
    data ? JSON.parse(data) : {}
    console.log(data)
  })
  .catch(error => {
    // Handle login error
    console.error('There was a problem with the login:', error);
    document.getElementById('message').textContent = "Login failed. Please try again.";
  });
});
