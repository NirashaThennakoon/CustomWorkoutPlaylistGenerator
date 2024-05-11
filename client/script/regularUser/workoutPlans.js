const MASONJSON = "application/vnd.mason+json";
const PLAINJSON = "application/json";
var baseURL = config.baseUrl;

$(document).ready(function() {
    var userId = localStorage.getItem('userId');
    url = "api/" + userId + "/workoutPlan";
    getResource(url, renderWorkoutPlans, baseURL);
});

// Define getResource function
function getResource(href, renderer, baseURL) {
    $.ajax({
        url: baseURL + href,
        success: renderer,
        error: renderError
    });
}

// Define button action function
function editButtonAction(event, href, renderer) {
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


// Define submitWorkoutPlan function
function submitWorkoutPlan(event) {
  event.preventDefault();

  let form = $('#workoutPlanForm');
  let data = {
      plan_name: $('#workoutPlanName').val(),
      duration: parseFloat($('#duration').val()),
      playlist_id: $('#playlist').val()
  };

  let method = form.attr("method");
  let action = form.attr("action");
  if (!action) {
    // If action attribute is not set, it's a create operation
    action = "/api/workoutPlan"; // Set action to the create endpoint
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
          getResource("/api/workoutPlan", renderWorkoutPlans, baseURL); // Refresh table after creation or update
          resetForm(); // Reset the form after submission
      },
      error: renderError
  });
}

function resetForm() {
  document.getElementById('workoutPlanForm').reset();
  // Additional reset logic if needed
}


function editWorkoutPlanForm(ctrl) {
    let form = $('#workoutPlanForm');
    form.attr("action", ctrl.href);
    form.attr("method", ctrl.method);
    ctrl.schema.required.forEach(function (property) {
        $("input[name='" + property + "']").attr("required", true);
    });
}

function editWorkoutPlan(body) {
    editWorkoutPlanForm(body["@controls"].edit);
    document.getElementById('workoutPlanName').value = body.plan_name;
    document.getElementById('duration').value = body.duration;
    document.getElementById('playlist').value = body.playlist_id;
    
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
function deleteWorkoutPlan(body) {
  let ctrl = body["@controls"].delete;
  sendData(ctrl.href, ctrl.method, null, function() {
      showModal("Workout successfully deleted");
      getResource("/api/workoutPlan", renderWorkoutPlans, baseURL); // Refresh table after deletion
  });
}

// Define getWorkoutPlans function
function getWorkoutPlans(event, workout) {
  event.preventDefault();
  let plansLinks = (workout["@controls"] && workout["@controls"].workoutplans) ? workout["@controls"].workoutplans.href : null;

  let plansBody = $("#plansTableBody");
  plansBody.empty();
  if (!plansLinks) {
      showModal("No workout plans available for this workout");
  }else{
    plansLinks.forEach(function(link) {
        plansBody.append(workoutPlanRow(link))
      });
  }
}

function renderWorkoutPlans(body) {
    $("div.navigation").empty();
    let tbody = $("#plansTableBody");
    tbody.append(detailedWorkoutPlanRow(body))
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

function detailedWorkoutPlanRow(workoutplan) {
    console.log(workoutplan)
    return "<tr><td>" + workoutplan.workout_plan_id    +
        "</td><td>" + workoutplan.plan_name +
        "</td><td>" + workoutplan.workouts_list.map(workout => workout.workout_name).join(', ') +
        "</tr>";
}

// Modify workoutPlanRow function to include the deleteConfirmation function
function workoutPlanRow(item) {
  let link = item["@controls"].item.href;

  return "<tr><td>" + item.plan_name +
          "</td><td>" + item.duration +
          "</td><td>" + item.playlist_id +
          "</td><td>" + item.workouts_list.map(workout => workout.workout_name).join(', ') +
          "</td><td>" +
              "<button onclick='editButtonAction(event, \"" + link + "\", editWorkoutPlan)'>Edit</button>" +
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


// Define renderWorkoutPlans function
function renderWorkoutPlans(body) {
    $("div.navigation").empty();
    let tbody = $("#workoutPlanTable tbody");
    tbody.empty();
    
    body["workout_plans_list"].forEach(function (item) {
        tbody.append(workoutPlanRow(item));
    });
}



