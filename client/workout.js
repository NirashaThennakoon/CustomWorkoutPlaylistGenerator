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

// Define renderWorkout function
function renderWorkout(body) {
    $("div.navigation").html(
        "<a href='" +
        body["@controls"].collection.href +
        "' onClick='followLink(event, this, renderWorkouts)'>collection</a> | "
    );
    $(".resulttable thead").empty();
    $(".resulttable tbody").empty();
    renderWorkoutForm(body["@controls"].edit);
    $("input[name='workout_name']").val(body.workout_name);
    $("input[name='duration']").val(body.duration);
    $("input[name='workout_intensity']").val(body.workout_intensity);
    $("input[name='equipment']").val(body.equipment);
    $("input[name='workout_type']").val(body.workout_type);
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
        url: href,
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
    let form = $("div.form form");
    data.workout_name = $("input[name='workout_name']").val();
    data.duration = $("input[name='duration']").val();
    data.workout_intensity = $("input[name='workout_intensity']").val();
    data.equipment = $("input[name='equipment']").val();
    data.workout_type = $("input[name='workout_type']").val();
    sendData(form.attr("action"), form.attr("method"), data, getSubmittedWorkout);
}

// Define renderWorkoutForm function
function renderWorkoutForm(ctrl) {
    console.log(ctrl)
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

// Define workoutRow function
function workoutRow(item) {
    let link = "<a href='" +
                item["@controls"].item.href +
                "' onClick='followLink(event, this, renderWorkout)'>show</a>";

    return "<tr><td>" + item.workout_name +
            "</td><td>" + item.duration +
            "</td><td>" + item.workout_intensity +
            "</td><td>" + item.equipment +
            "</td><td>" + item.workout_type +
            "</td><td>" + link + "</td></tr>";
}

// Define renderWorkouts function
function renderWorkouts(body) {
    $("div.navigation").empty();
    let tbody = $("#workoutTable tbody");
    tbody.empty();
    body["workout list"].forEach(function (item) {
        tbody.append(workoutRow(item));
    });
    console.log(body)
    // renderWorkoutForm(body["@controls"]["edit"]);
}
