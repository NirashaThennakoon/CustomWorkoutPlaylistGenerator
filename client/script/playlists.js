const MASONJSON = "application/vnd.mason+json";
const PLAINJSON = "application/json";
const baseURL = config.baseUrl;

$(document).ready(function() {
    getResource("/api/playlist", renderPlaylists, baseURL);
});

function getResource(href, renderer, baseURL) {
    $.ajax({
        url: baseURL + href,
        success: renderer,
        error: renderError
    });
}

function buttonAction(event, href, renderer) {
    event.preventDefault();
    getResource(href, renderer, baseURL);
}

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
    $("div.notification").html("<p class='error-message'>" + msg + "</p>");
}

function renderMsg(msg) {
    $("div.notification").html("<p class='msg'>" + msg + "</p>");
}

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

function submitPlaylist(event) {
    event.preventDefault();

    let form = $('#playlistForm');
    let data = {
        playlist_name: $('#playlistName').val(),
        playlist_duration: parseFloat($('#playlistDuration').val())
    };

    let method = form.attr("method");
    let action = form.attr("action");
    if (!action) {
        action = "/api/playlists";
    }

    if (!method) {
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
                renderMsg("Successfully created playlist");
            } else if (method === "PUT") {
                renderMsg("Successfully updated playlist");
                document.getElementById('createBtn').removeAttribute('disabled'); // Enable Create button
                document.getElementById('editBtn').setAttribute('disabled', true); // Disable Edit button
            }
            getResource("/api/playlists", renderPlaylists, baseURL);
            resetForm();
        },
        error: renderError
    });
}

function resetForm() {
    document.getElementById('playlistForm').reset();
    document.getElementById('createBtn').removeAttribute('disabled'); // Enable Create button
    document.getElementById('editBtn').setAttribute('disabled', true); // Disable Edit button
}

function editPlaylistForm(ctrl) {
    let form = $('#playlistForm');
    form.attr("action", ctrl.href);
    form.attr("method", ctrl.method);
    ctrl.schema.required.forEach(function(property) {
        $("input[name='" + property + "']").attr("required", true);
    });
}

function editPlaylist(body) {
    editPlaylistForm(body["@controls"].edit);
    document.getElementById('playlistName').value = body.playlist_name;
    document.getElementById('playlistDuration').value = body.playlist_duration;

    document.getElementById('createBtn').setAttribute('disabled', true);
    document.getElementById('editBtn').removeAttribute('disabled');
}

function deleteConfirmation(event, body) {
    event.preventDefault();
    showConfirmationDialog("Are you sure you want to delete this playlist?", function(confirmed) {
        if (confirmed) {
            deletePlaylist(body);
        }
    });
}

function deletePlaylist(body) {
    let ctrl = body["@controls"].delete;
    sendData(ctrl.href, ctrl.method, null, function() {
        showModal("Playlist successfully deleted");
        getResource("/api/playlists", renderPlaylists, baseURL);
    });
}

function renderPlaylists(body) {
    $("div.navigation").empty();
    let tbody = $("#playlistTable tbody");
    tbody.empty();
    body["playlists"].forEach(function(item) {
        tbody.append(playlistRow(item));
    });
}

function playlistRow(item) {
    let link = item["@controls"].item.href;

    return "<tr><td>" + item.playlist_name +
        "</td><td>" + item.playlist_duration +
        "</td><td>" +
        "<button onclick='buttonAction(event, \"" + link + "\", editPlaylist)'>Edit</button>" +
        "<button onclick='deleteConfirmation(event, " + JSON.stringify(item) + ")'>Delete</button>" +
        "<button onclick='getSongs(event, " + JSON.stringify(item) + ")'>View Songs</button>" +
        "</td></tr>";
}

function showConfirmationDialog(message, callback) {
    let confirmationModal = document.getElementById("confirmationModal");
    let confirmationMessage = document.getElementById("confirmationMessage");
    let confirmBtn = document.getElementById("confirmBtn");
    let cancelBtn = document.getElementById("cancelBtn");

    confirmationMessage.textContent = message;
    confirmationModal.style.display = "block";

    confirmBtn.onclick = function() {
        confirmationModal.style.display = "none";
        callback(true);
    };

    cancelBtn.onclick = function() {
        confirmationModal.style.display = "none";
        callback(false);
    };
}

function showModal(message) {
    let modal = document.getElementById("myModal");
    let modalMessage = document.getElementById("modalMessage");
    modalMessage.textContent = message;
    modal.style.display = "block";

    let closeButton = document.getElementsByClassName("close")[0];
    closeButton.onclick = function() {
        modal.style.display = "none";
    }

    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }
}

function getSongs(event, playlist) {
    event.preventDefault();
    let songsLink = playlist["@controls"].up.href;

    $.ajax({
        url: baseURL + songsLink,
        success: function(songs) {
            showSongs(songs);
        },
        error: renderError
    });
}

function showSongs(songs) {
    let songsTableBody = $("#songsTableBody");
    songsTableBody.empty();

    if ($.isEmptyObject(songs["Songs"])) {
        songsTableBody.append(
            "<tr><td colspan='4'>No songs available for this playlist</td></tr>"
        );
    } else {
        songs["Songs"].forEach(function(song) {
            songsTableBody.append(
                "<tr><td>" + song.song_name + "</td>" +
                "<td>" + song.song_artist + "</td>" +
                "<td>" + song.song_genre + "</td>" +
                "<td>" + song.song_duration + "</td></tr>"
            );
        });
    }

    let songsModal = document.getElementById("songsModal");
    songsModal.style.display = "block";

    let closeButton = songsModal.querySelector(".close");
    closeButton.onclick = function() {
        songsModal.style.display = "none";
    };

    window.onclick = function(event) {
        if (event.target == songsModal) {
            songsModal.style.display = "none";
        }
    };
}
