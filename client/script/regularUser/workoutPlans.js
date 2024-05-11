const MASONJSON = "application/vnd.mason+json";
const PLAINJSON = "application/json";
var baseURL = config.baseUrl;

// JavaScript for rendering workout plans and workouts with clickable headings

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

// Define renderWorkoutPlans function
function renderWorkoutPlans(body) {
    let list = $("#workoutPlanList");
    list.empty();
    body["workout_plans_list"].forEach(function (item) {
        list.append(workoutPlanRow(item));
    });
}

// Function to render each workout plan
function workoutPlanRow(item) {
    let html = "<li>";
    html += "<h3 class='collapsible'>" + item.plan_name + "</h3>";
    html += "<div class='content'>";
    html += "<h4>Workouts</h4>";
    html += "<ul>";
    item.workouts_list.forEach(function(workout) {
        html += "<li>" + workout.workout_name + "</li>";
    });
    html += "</ul>";
    html += "</div>";
    html += "</li>";
    return html;
}

// Add functionality for collapsible sections
$(document).on("click", ".collapsible", function() {
    $(this).toggleClass("active");
    var content = $(this).next();
    if (content.css("display") === "block") {
        content.css("display", "none");
    } else {
        content.css("display", "block");
    }
});
