const MASONJSON = "application/vnd.mason+json";
const PLAINJSON = "application/json";
var baseURL = config.baseUrl;

$(document).ready(function () {
  var userId = localStorage.getItem("userId");
  console.log(userId);
  url = "api/" + userId + "/workoutPlan";
  getResource(url, renderWorkoutPlans, baseURL);
});

// Define getResource function
function getResource(href, renderer, baseURL) {
  $.ajax({
    url: baseURL + href,
    success: renderer,
    error: renderError,
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
  if (jqxhr.getResponseHeader("Content-Type") === MASONJSON) {
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
    error: renderError,
  });
}

// Define submitWorkoutPlan function
function submitWorkoutPlan(event) {
  event.preventDefault();

  let form = $("#workoutPlanForm");
  let data = {
    plan_name: $("#workoutPlanName").val(),
    workout_ids: getSelectedWorkouts(),
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
    success: function (response) {
      if (method === "POST") {
        renderMsg("Successfully created workout");
      } else if (method === "PUT") {
        renderMsg("Successfully updated workout");
      }
      getResource("/api/workoutPlan/", renderWorkoutPlans, baseURL); // Refresh table after creation or update
      resetForm(); // Reset the form after submission
    },
    error: renderError,
  });
}

function resetForm() {
  document.getElementById("workoutPlanForm").reset();
  document.getElementById("createBtn").removeAttribute("disabled"); // Enable Create button
  document.getElementById("editBtn").setAttribute("disabled", true); // Disable Edit button
  // Additional reset logic if needed
}

function editWorkoutPlanForm(ctrl) {
  let form = $("#workoutPlanForm");
  form.attr("action", ctrl.href);
  form.attr("method", ctrl.method);
  ctrl.schema.required.forEach(function (property) {
    $("input[name='" + property + "']").attr("required", true);
  });
}

function editWorkoutPlan(body) {
  console.log(body);
  editWorkoutPlanForm(body["@controls"].edit);
  document.getElementById("workoutPlanName").value = body.plan_name;
  document.getElementById("createBtn").setAttribute("disabled", true);
  document.getElementById("editBtn").removeAttribute("disabled");
  let selectedWorkouts = [];
  body["workouts_list"].forEach(function (workout) {
    selectedWorkouts.push(workout.workout_id);
  });

  // Iterate through each checkbox and mark it as checked if its value is in the selectedWorkouts array
  $(".workoutCheckbox").each(function () {
    let checkboxValue = $(this).val();
    let workoutId = parseInt(checkboxValue.match(/\d+/)[0]);
    if (selectedWorkouts.includes(workoutId)) {
      $(this).prop("checked", true);
    } else {
      $(this).prop("checked", false);
    }
  });
}

// Function to display custom confirmation dialog
function showConfirmationDialog(message, callback) {
  let confirmationModal = document.getElementById("confirmationModal");
  let confirmationMessage = document.getElementById("confirmationMessage");
  let confirmBtn = document.getElementById("confirmBtn");
  let cancelBtn = document.getElementById("cancelBtn");

  confirmationMessage.textContent = message;
  confirmationModal.style.display = "block";

  confirmBtn.onclick = function () {
    confirmationModal.style.display = "none";
    callback(true); // Call the callback function with true (confirmed)
  };

  cancelBtn.onclick = function () {
    confirmationModal.style.display = "none";
    callback(false); // Call the callback function with false (cancelled)
  };
}

// Define deleteConfirmation function
function deleteConfirmation(event, body) {
  event.preventDefault();
  showConfirmationDialog(
    "Are you sure you want to delete this workout plan?",
    function (confirmed) {
      if (confirmed) {
        deleteWorkoutPlan(body);
      }
    }
  );
}

// Modify deleteWorkoutPlan function to include refreshing the table after deletion and showing success message
function deleteWorkoutPlan(body) {
  console.log(body["@controls"]);
  let ctrl = body["@controls"].delete;
  sendData(ctrl.href, ctrl.method, null, function () {
    showModal("Workout plan successfully deleted");
    getResource("/api/workoutPlan", renderWorkoutPlans, baseURL); // Refresh table after deletion
  });
}

// Define getWorkoutPlans function
function getWorkoutPlans(event, workout) {
  event.preventDefault();
  let plansLinks =
    workout["@controls"] && workout["@controls"].workoutplans
      ? workout["@controls"].workoutplans.href
      : null;

  let plansBody = $("#plansTableBody");
  plansBody.empty();
  if (!plansLinks) {
    showModal("No workout plans available for this workout");
  } else {
    plansLinks.forEach(function (link) {
      plansBody.append(workoutPlanRow(link));
    });
  }
}

function renderWorkoutPlans(body) {
  $("div.navigation").empty();
  let tbody = $("#plansTableBody");
  tbody.append(detailedWorkoutPlanRow(body));
  let workoutPlansModal = document.getElementById("workoutPlansModal");
  workoutPlansModal.style.display = "block";

  // Close the modal when clicking on the close button
  let closeButton = workoutPlansModal.querySelector(".close");
  closeButton.onclick = function () {
    workoutPlansModal.style.display = "none";
  };

  // Close the modal when clicking anywhere outside of it
  window.onclick = function (event) {
    if (event.target == workoutPlansModal) {
      workoutPlansModal.style.display = "none";
    }
  };
}

function detailedWorkoutPlanRow(workoutplan) {
  console.log(workoutplan);
  return (
    "<tr><td>" +
    workoutplan.workout_plan_id +
    "</td><td>" +
    workoutplan.plan_name +
    "</td><td>" +
    workoutplan.workouts_list
      .map((workout) => workout.workout_name)
      .join(", ") +
    "</tr>"
  );
}

// Modify workoutPlanRow function to include the deleteConfirmation function
function workoutPlanRow(item) {
  let itemLink = item["@controls"].item.href;

  return (
    "<tr><td>" +
    item.plan_name +
    "</td><td>" +
    item.duration +
    "</td><td>" +
    item.playlist_id +
    "</td><td>" +
    item.workouts_list.map((workout) => workout.workout_name).join(", ") +
    "</td><td>" +
    "<button type='button' class='btn me-3' style='background-color: #4a4e69; color: white;' onclick='editButtonAction(event, \"" +
    itemLink +
    "\", editWorkoutPlan)'>Edit</button>" +
    "<button type='button' class='btn btn-danger' onclick='deleteConfirmation(event, " +
    JSON.stringify(item) +
    ")'>Delete</button>" +
    "<button type='button' class='btn mx-3' style='background-color: #008000; color: white;' onclick='getWorkoutPlans(event, " +
    JSON.stringify(item) +
    ")'>View Plans</button>" +
    "</td></tr>"
  );
}

// Function to display modal with message
function showModal(message) {
  let modal = document.getElementById("myModal");
  let modalMessage = document.getElementById("modalMessage");
  modalMessage.textContent = message;
  modal.style.display = "block";

  // Close the modal when clicking on the close button
  let closeButton = document.getElementsByClassName("close")[0];
  closeButton.onclick = function () {
    modal.style.display = "none";
  };

  // Close the modal when clicking anywhere outside of it
  window.onclick = function (event) {
    if (event.target == modal) {
      modal.style.display = "none";
    }
  };
}

// Define renderWorkoutPlans function
function renderWorkoutPlans(body) {
  $("div.navigation").empty();
  let tbody = $("#workoutPlanTable tbody");
  tbody.empty();
  body["workout_plans_list"].forEach(function (item) {
    tbody.append(workoutPlanRow(item));
  });
  populateWorkoutsDropdown(body["@controls"].item.href);
}

function populateWorkoutsDropdown(link) {
  getResource(link, renderDropDown, baseURL);
}

function renderDropDown(body) {
  let tbody = $("#workoutsSelectionTable tbody");
  tbody.empty();
  body["workout list"].forEach(function (workout) {
    tbody.append(populateOptionForDropdown(workout));
  });
}

function populateOptionForDropdown(workout) {
  return (
    "<tr><td hidden>" +
    workout.workout_id +
    "</td><td>" +
    workout.workout_name +
    "</td><td>" +
    workout.workout_intensity +
    "</td><td>" +
    workout.duration +
    "</td><td>" +
    workout.equipment +
    "</td><td>" +
    workout.workout_type +
    "</td><td style='text-align: center;'>" +
    "<input type='checkbox' class='workoutCheckbox' value=" +
    workout.workout_id +
    "</td></tr>"
  );
}

function selectAllWorkouts(checkbox) {
  $(".workoutCheckbox").prop("checked", checkbox.checked);
}

function getSelectedWorkouts() {
  let selectedWorkouts = [];
  $(".workoutCheckbox:checked").each(function () {
    selectedWorkouts.push($(this).val());
  });
  return selectedWorkouts;
}

function scrollToTarget() {
  var targetElement = document.getElementById("workoutPlanTable");
  targetElement.scrollIntoView({ behavior: "smooth" });
}
