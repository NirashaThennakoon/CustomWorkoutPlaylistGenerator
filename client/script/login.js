document.getElementById('login-form').addEventListener('submit', function(e) {
    const baseURL = config.baseUrl;
    e.preventDefault();
  
    var email = document.getElementById('email').value;
    var password = document.getElementById('password').value;
  
    // // Basic email validation
    // if (!isValidEmail(email)) {
    //   document.getElementById('message').textContent = "Please enter a valid email address.";
    //   return;
    // }
  
    var formData = {
      email: email,
      password: password
    };
  
    fetch(baseURL+'/api/user/'+email, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(formData)
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      var userId = data.user_id;
      console.log(userId)
      localStorage.setItem('userId', userId);

      if (data.user_type === 'admin') {
        // Redirect to admin dashboard
        window.location.href = 'adminDashboard.html';
      } else {
        // Handle successful login for other users
        window.location.href = 'regularUser/workoutplans.html';
      }
    })
    .catch(error => {
      // Handle login error
      console.error('There was a problem with the login:', error);
      document.getElementById('message').textContent = "Login failed. Please try again.";
    });
  });