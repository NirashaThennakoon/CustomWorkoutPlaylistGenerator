const MASONJSON = "application/vnd.mason+json";
const PLAINJSON = "application/json";
var baseURL = config.baseUrl;
const songURL = "api/song";

$(document).ready(function () {
  getResource(songURL, renderSongs, baseURL);
});

function getResource(href, renderer, baseURL) {
  $.ajax({
    url: baseURL + href,
    success: renderer,
    error: renderError,
  });
}

function editButtonAction(event, href, renderer) {
  event.preventDefault();
  getResource(href, renderer, baseURL);
}

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
    error: renderError,
  });
}

function submitSong(event) {
  event.preventDefault();

  let form = $("#songForm");
  let data = {
    song_name: $("#songName").val(),
    song_artist: $("#songArtist").val(),
    song_genre: $("#songGenre").val(),
    song_duration: parseFloat($("#songDuration").val()),
  };

  let method = form.attr("method");
  let action = form.attr("action");
  if (!action) {
    action = songURL;
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
    success: function (response) {
      if (method === "POST") {
        renderMsg("Successfully created song");
      } else if (method === "PUT") {
        renderMsg("Successfully updated song");
        document.getElementById("createBtn").removeAttribute("disabled"); // Enable Create button
        document.getElementById("editBtn").setAttribute("disabled", true); // Disable Edit button
      }
      getResource(songURL, renderSongs, baseURL);
      resetForm();
    },
    error: renderError,
  });
}

function resetForm() {
  document.getElementById("songForm").reset();
  document.getElementById("createBtn").removeAttribute("disabled"); // Enable Create button
  document.getElementById("editBtn").setAttribute("disabled", true); // Disable Edit button
}

function editSongForm(ctrl) {
  let form = $("#songForm");
  form.attr("action", ctrl.href);
  form.attr("method", ctrl.method);
  ctrl.schema.required.forEach(function (property) {
    $("input[name='" + property + "']").attr("required", true);
  });
}

function editSong(body) {
  editSongForm(body["@controls"].edit);
  document.getElementById("songName").value = body.song_name;
  document.getElementById("songArtist").value = body.song_artist;
  document.getElementById("songGenre").value = body.song_genre;
  document.getElementById("songDuration").value = body.song_duration;

  document.getElementById("createBtn").setAttribute("disabled", true);
  document.getElementById("editBtn").removeAttribute("disabled");
}

function deleteConfirmation(event, body) {
  event.preventDefault();
  showConfirmationDialog(
    "Are you sure you want to delete this song?",
    function (confirmed) {
      if (confirmed) {
        deleteSong(body);
      }
    }
  );
}

function deleteSong(body) {
  let ctrl = body["@controls"].delete;
  sendData(ctrl.href, ctrl.method, null, function () {
    showModal("Song successfully deleted");
    getResource(songURL, renderSongs, baseURL);
  });
}

function renderSongs(body) {
  $("div.navigation").empty();
  let tbody = $("#songTable tbody");
  tbody.empty();
  body["song list"].forEach(function (item) {
    tbody.append(songRow(item));
  });
}

function playlistRow(link) {
  console.log(link);
  getResource(link.href, renderPlaylists, baseURL);
}

function getPlaylists(event, song) {
  event.preventDefault();
  let playlistsLinks =
    song["@controls"] && song["@controls"].playlists
      ? song["@controls"].playlists.href
      : null;
  let playlistBody = $("#detailedPlaylistTable tbody");
  playlistBody.empty();
  if (!playlistsLinks) {
    showModal("No playlist available for this song");
  } else {
    playlistsLinks.forEach(function (link) {
      playlistBody.append(playlistRow(link));
    });
  }
}

function renderPlaylists(body) {
  $("div.navigation").empty();
  let tbody = $("#detailedPlaylistTable tbody");
  tbody.append(detailedPlaylistRow(body));
  let playlistsModal = document.getElementById("playlistsModal");
  playlistsModal.style.display = "block";

  // Close the modal when clicking on the close button
  let closeButton = playlistsModal.querySelector(".close");
  closeButton.onclick = function () {
    playlistsModal.style.display = "none";
  };

  // Close the modal when clicking anywhere outside of it
  window.onclick = function (event) {
    if (event.target == playlistsModal) {
      playlistsModal.style.display = "none";
    }
  };
}

function detailedPlaylistRow(playlist) {
  return (
    "<tr><td>" +
    playlist.playlist_id +
    "</td><td>" +
    playlist.playlist_name +
    "</td><td>" +
    playlist.songs_list.map((song) => song.song_name).join(", ") +
    "</tr>"
  );
}

function songRow(item) {
  let link = item["@controls"].item.href;

  return (
    "<tr><td>" +
    item.song_name +
    "</td><td>" +
    item.song_artist +
    "</td><td>" +
    item.song_genre +
    "</td><td>" +
    item.song_duration +
    "</td><td>" +
    "<button class='btn btn-warning me-3' onclick='editButtonAction(event, \"" +
    link +
    "\", editSong)'>Edit</button>" +
    "<button class='btn btn-danger' onclick='deleteConfirmation(event, " +
    JSON.stringify(item) +
    ")'>Delete</button>" +
    "<button class='btn btn-info mx-3' onclick='getPlaylists(event, " +
    JSON.stringify(item) +
    ")'>View Playlists</button>" +
    "</td></tr>"
  );
}

function showConfirmationDialog(message, callback) {
  let confirmationModal = document.getElementById("confirmationModal");
  let confirmationMessage = document.getElementById("confirmationMessage");
  let confirmBtn = document.getElementById("confirmBtn");
  let cancelBtn = document.getElementById("cancelBtn");

  confirmationMessage.textContent = message;
  confirmationModal.style.display = "block";

  confirmBtn.onclick = function () {
    confirmationModal.style.display = "none";
    callback(true);
  };

  cancelBtn.onclick = function () {
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
  closeButton.onclick = function () {
    modal.style.display = "none";
  };

  window.onclick = function (event) {
    if (event.target == modal) {
      modal.style.display = "none";
    }
  };
}
