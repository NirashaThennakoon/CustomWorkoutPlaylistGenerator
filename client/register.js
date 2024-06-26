document.getElementById('register-form').addEventListener('submit', function(e) {
    e.preventDefault();
  
    var email = document.getElementById('email').value;
    var password = document.getElementById('password').value;
    var height = parseFloat(document.getElementById('height').value);
    var weight = parseFloat(document.getElementById('weight').value);
    var userType = document.getElementById('user-type').value;
  
    // Basic email validation
    if (!isValidEmail(email)) {
      document.getElementById('message').textContent = "Please enter a valid email address.";
      return;
    }
  
    var formData = {
      email: email,
      password: password,
      height: height,
      weight: weight,
      user_type: userType
    };
  
    fetch('http://127.0.0.1:5000/api/user/register/', {
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
      // Handle successful registration
      console.log(data);
      document.getElementById('message').textContent = "Registration successful!";
      window.location.href = "login.html";
    })
    .catch(error => {
      // Handle registration error
      console.error('There was a problem with the registration:', error);
      document.getElementById('message').textContent = "Registration failed. Please try again.";
    });
  });
  
  function isValidEmail(email) {
    // Basic email validation regex
    var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }
  