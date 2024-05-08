const MASONJSON = "application/vnd.mason+json";
const PLAINJSON = "application/json";
baseURL = "http://127.0.0.1:5000"

$(document).ready(function() {
    // Your jQuery-dependent code here
    getResource("/api/workout", renderWorkouts, baseURL);
});

// Define getResource function
function getResource(href, renderer, baseURL) {
    $.ajax({
        url: baseURL + href,
        success: renderer,
        error: renderError
    });
}

// Define followLink function
function followLink(event, a, renderer) {
    event.preventDefault();
    getResource($(a).attr("href"), renderer, baseURL);
}

// Define button action function
function buttonAction(event, href, renderer) {
    event.preventDefault();
    getResource(href, renderer, baseURL);
}

// Define renderError function
function renderError(jqxhr) {
  let msg;
  if (jqxhr.getResponseHeader('Content-Type') === MASONJSON) {
      let responseBody = JSON.parse(jqxhr.responseText);
      if (responseBody["@error"]) {
          msg = responseBody["@error"]["@message"];
      } else {
          msg = "An error occurred. Please try again later.";
      }
  } else if (jqxhr.responseText) {
      msg = jqxhr.responseText;
  } else if (jqxhr.statusText) {
      msg = jqxhr.statusText;
  } else {
      msg = "An error occurred. Please try again later.";
  }
  // Apply error-message class to the error message
  $("div.notification").html("<p class='error-message'>" + msg + "</p>");
}

// Define renderMsg function
function renderMsg(msg) {
    $("div.notification").html("<p class='msg'>" + msg + "</p>");
}

// Define sendData function
function sendData(href, method, item, postProcessor) {
    $.ajax({
        url: baseURL + href,
        type: method,
        data: JSON.stringify(item),
        contentType: PLAINJSON,
        processData: false,
        success: postProcessor,
        error: renderError
    });
}

// Define getSubmittedWorkout function
function getSubmittedWorkout(data, status, jqxhr) {
    renderMsg("Successfully updated workout");
    // let href = jqxhr.getResponseHeader("Location");
    // if (href) {
    //     getResource(href, appendSensorRow);
    // }
}

// Define submitWorkout function
function submitWorkout(event) {
  event.preventDefault();

  let form = $('#workoutForm');
  let data = {
      workout_name: $('#workoutName').val(),
      duration: parseFloat($('#duration').val()),
      workout_intensity: $('#workoutIntensity').val(),
      equipment: $('#equipment').val(),
      workout_type: $('#workoutType').val()
  };

  let method = form.attr("method");
  let action = form.attr("action");
  if (!action) {
    // If action attribute is not set, it's a create operation
    action = "/api/workout"; // Set action to the create endpoint
  }

  if (!method) {
    // If action attribute is not set, it's a create operation
    method = "POST";
  }


  $.ajax({
      url: baseURL + action,
      type: method,
      data: JSON.stringify(data),
      contentType: PLAINJSON,
      processData: false,
      success: function(response) {
          if (method === "POST") {
              renderMsg("Successfully created workout");
          } else if (method === "PUT") {
              renderMsg("Successfully updated workout");
          }
          getResource("/api/workout", renderWorkouts, baseURL); // Refresh table after creation or update
          resetForm(); // Reset the form after submission
      },
      error: renderError
  });
}

function resetForm() {
  document.getElementById('workoutForm').reset();
  // Additional reset logic if needed
}


function editWorkoutForm(ctrl) {
    let form = $('#workoutForm');
    form.attr("action", ctrl.href);
    form.attr("method", ctrl.method);
    ctrl.schema.required.forEach(function (property) {
        $("input[name='" + property + "']").attr("required", true);
    });
}

function editWorkout(body) {
    editWorkoutForm(body["@controls"].edit);
    document.getElementById('workoutName').value = body.workout_name;
    document.getElementById('duration').value = body.duration;
    document.getElementById('workoutIntensity').value = body.workout_intensity;
    document.getElementById('equipment').value = body.equipment;
    document.getElementById('workoutType').value = body.workout_type;
    
    document.getElementById('createBtn').setAttribute('disabled', true);
    document.getElementById('editBtn').removeAttribute('disabled');
}

// Function to display custom confirmation dialog
function showConfirmationDialog(message, callback) {
  let confirmationModal = document.getElementById("confirmationModal");
  let confirmationMessage = document.getElementById("confirmationMessage");
  let confirmBtn = document.getElementById("confirmBtn");
  let cancelBtn = document.getElementById("cancelBtn");

  confirmationMessage.textContent = message;
  confirmationModal.style.display = "block";

  confirmBtn.onclick = function() {
      confirmationModal.style.display = "none";
      callback(true); // Call the callback function with true (confirmed)
  };

  cancelBtn.onclick = function() {
      confirmationModal.style.display = "none";
      callback(false); // Call the callback function with false (cancelled)
  };
}

// Define deleteConfirmation function
function deleteConfirmation(event, body) {
  event.preventDefault();
  showConfirmationDialog("Are you sure you want to delete this workout?", function(confirmed) {
      if (confirmed) {
          deleteWorkout(body);
      }
  });
}

// Modify deleteWorkout function to include refreshing the table after deletion and showing success message
function deleteWorkout(body) {
  let ctrl = body["@controls"].delete;
  sendData(ctrl.href, ctrl.method, null, function() {
      showModal("Workout successfully deleted");
      getResource("/api/workout", renderWorkouts, baseURL); // Refresh table after deletion
  });
}

// Define getWorkoutPlans function
function getWorkoutPlans(event, workout) {
  event.preventDefault();
  let plansLink = workout["@controls"].up.href;

  $.ajax({
      url: baseURL + plansLink,
      success: function(plans) {
          showWorkoutPlans(plans);
      },
      error: renderError
  });
}

// Function to display workout plans in a popup table
function showWorkoutPlans(plans) {
  let plansTableBody = $("#plansTableBody");
  plansTableBody.empty();

  if ($.isEmptyObject(plans)) {
    plansTableBody.append(
        "<tr><td colspan='2'>No workout plans available for this workout</td></tr>"
    );
  } else {
    plans["workout list"].forEach(function(plan) {
        plansTableBody.append(
            "<tr><td>" + plan.workout_plan_id + "</td></tr>"
        );
    });
  }

  let workoutPlansModal = document.getElementById("workoutPlansModal");
  workoutPlansModal.style.display = "block";

  // Close the modal when clicking on the close button
  let closeButton = workoutPlansModal.querySelector(".close");
  closeButton.onclick = function() {
      workoutPlansModal.style.display = "none";
  };

  // Close the modal when clicking anywhere outside of it
  window.onclick = function(event) {
      if (event.target == workoutPlansModal) {
          workoutPlansModal.style.display = "none";
      }
  };
}



// Modify workoutRow function to include the deleteConfirmation function
function workoutRow(item) {
  let link = item["@controls"].item.href;

  return "<tr><td>" + item.workout_name +
          "</td><td>" + item.duration +
          "</td><td>" + item.workout_intensity +
          "</td><td>" + item.equipment +
          "</td><td>" + item.workout_type +
          "</td><td>" +
              "<button onclick='buttonAction(event, \"" + link + "\", editWorkout)'>Edit</button>" +
              "<button onclick='deleteConfirmation(event, " + JSON.stringify(item) + ")'>Delete</button>" +
              "<button onclick='getWorkoutPlans(event, " + JSON.stringify(item) + ")'>View Plans</button>" +
          "</td></tr>"; 
}

// Function to display modal with message
function showModal(message) {
  let modal = document.getElementById("myModal");
  let modalMessage = document.getElementById("modalMessage");
  modalMessage.textContent = message;
  modal.style.display = "block";

  // Close the modal when clicking on the close button
  let closeButton = document.getElementsByClassName("close")[0];
  closeButton.onclick = function() {
      modal.style.display = "none";
  }

  // Close the modal when clicking anywhere outside of it
  window.onclick = function(event) {
      if (event.target == modal) {
          modal.style.display = "none";
      }
  }
}


// Define renderWorkouts function
function renderWorkouts(body) {
    $("div.navigation").empty();
    let tbody = $("#workoutTable tbody");
    tbody.empty();
    body["workout list"].forEach(function (item) {
        tbody.append(workoutRow(item));
    });
    // renderWorkoutForm(body["@controls"]["edit"]);
}



