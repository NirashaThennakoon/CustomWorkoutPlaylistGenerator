const MASONJSON = "application/vnd.mason+json";
const PLAINJSON = "application/json";
baseURL = "http://127.0.0.1:5000"
// Ensure jQuery is loaded before executing any jQuery-dependent code
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

// Define followLink function
function buttonAction(event, href, renderer) {
    event.preventDefault();
    getResource(href, renderer, baseURL);
}

// Define renderError function
function renderError(jqxhr) {
    let msg = jqxhr.responseJSON["@error"]["@message"];
    $("div.notification").html("<p class='error'>" + msg + "</p>");
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

    let data = {};
    let form = $('#workoutForm');
    data.workout_name = document.getElementById('workoutName').value;
    data.duration = parseFloat(document.getElementById('duration').value);
    data.workout_intensity = document.getElementById('workoutIntensity').value;
    data.equipment = document.getElementById('equipment').value;
    data.workout_type = document.getElementById('workoutType').value;
    sendData(form.attr("action"), form.attr("method"), data, getSubmittedWorkout);
}

// Define renderWorkoutForm function
function renderWorkoutForm(ctrl) {
    let form = $("<form>");
    let workout_name = ctrl.schema.properties.workout_name;
    let duration = ctrl.schema.properties.duration;
    let workout_intensity = ctrl.schema.properties.workout_intensity;
    let equipment = ctrl.schema.properties.equipment;
    let workout_type = ctrl.schema.properties.workout_type;
    form.attr("action", ctrl.href);
    form.attr("method", ctrl.method);
    form.submit(submitWorkout);
    form.append("<label>" + workout_name + "</label>");
    form.append("<input type='text' name='workout_name'>");
    form.append("<label>" + duration + "</label>");
    form.append("<input type='text' name='duration'>");
    form.append("<label>" + workout_intensity + "</label>");
    form.append("<input type='text' name='workout_intensity'>");
    form.append("<label>" + equipment + "</label>");
    form.append("<input type='text' name='equipment'>");
    form.append("<label>" + workout_type + "</label>");
    form.append("<input type='text' name='workout_type'>");
    ctrl.schema.required.forEach(function (property) {
        $("input[name='" + property + "']").attr("required", true);
    });
    form.append("<input type='submit' name='submit' value='Submit'>");
    $("div.form").html(form);
}

function editWorkoutForm(ctrl) {
    let form = $('#workoutForm');
    // let workout_name = ctrl.schema.properties.workout_name;
    // let duration = ctrl.schema.properties.duration;
    // let workout_intensity = ctrl.schema.properties.workout_intensity;
    // let equipment = ctrl.schema.properties.equipment;
    // let workout_type = ctrl.schema.properties.workout_type;
    form.attr("action", ctrl.href);
    form.attr("method", ctrl.method);
    // form.submit(submitWorkout);

    ctrl.schema.required.forEach(function (property) {
        $("input[name='" + property + "']").attr("required", true);
    });
    // form.append("<button type='button' name='Edit' value='Edit' id='editBtn'>");
    $("div.form").html(form);
}

// // Define renderWorkout function
// function renderWorkout(body) {
//     $("div.navigation").html(
//         "<a href='" +
//         body["@controls"].collection.href +
//         "' onClick='followLink(event, this, renderWorkouts)'>collection</a> | "
//     );
//     $(".resulttable thead").empty();
//     $(".resulttable tbody").empty();
//     renderWorkoutForm(body["@controls"].edit);
//     $("input[name='workout_name']").val(body.workout_name);
//     $("input[name='duration']").val(body.duration);
//     $("input[name='workout_intensity']").val(body.workout_intensity);
//     $("input[name='equipment']").val(body.equipment);
//     $("input[name='workout_type']").val(body.workout_type);
// }

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

// Define workoutRow function
function workoutRow(item) {
    let edit_link = item["@controls"].item.href;

    return "<tr><td>" + item.workout_name +
            "</td><td>" + item.duration +
            "</td><td>" + item.workout_intensity +
            "</td><td>" + item.equipment +
            "</td><td>" + item.workout_type +
            "</td><td>" +
                "<button onclick='buttonAction(event, \"" + edit_link + "\", editWorkout)'>Edit</button>" +
                // "<button onclick='deleteWorkout(" + item.id + ")'>Delete</button>" +
                // "<button onclick='planWorkout(" + item.id + ")'>Workout Plan</button>" +
            "</td></tr>"; 
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
