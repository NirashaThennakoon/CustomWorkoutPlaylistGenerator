document.getElementById('login-form').addEventListener('submit', function(e) {
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
  
    fetch('http://127.0.0.1:5000/api/user/login/', {
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
      // Handle successful login
      console.log(data);
      document.getElementById('message').textContent = "Login successful!";
    })
    .catch(error => {
      // Handle login error
      console.error('There was a problem with the login:', error);
      document.getElementById('message').textContent = "Login failed. Please try again.";
    });
  });