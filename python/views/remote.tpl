% if not defined("embedded") or not embedded:
%   include("header.tpl", title="Remote")
% else:
<!DOCTYPE html>
<html lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1.0"/>
  <title>PiFinder - Remote</title>
  <link href="/css/material_icons.css" rel="stylesheet">
  <link href="/css/materialize.css" type="text/css" rel="stylesheet" media="screen,projection"/>
  <link href="/css/style.css?v=20260504-lite-remote-landscape4" type="text/css" rel="stylesheet" media="screen,projection"/>
</head>
<body class="grey darken-3 embedded-remote-body">
  <main class="embedded-remote-main">
% end

<div id="error" class="error-message"></div>
<div class="remote-shell">
    <div class="remote-screen-panel">
        <img id="image" src="" alt="PiFinder Screen" class="pifinder-screen z-depth-2">
    </div>
    <div class="remote-grid">
        <button class="btn remote-button" aria-label="Left" onclick="buttonClicked(this, 'A')">&larr;</button>
        <button class="btn remote-button" aria-label="Up" onclick="buttonClicked(this, 'B')">&uarr;</button>
        <button class="btn remote-button" aria-label="Down" onclick="buttonClicked(this, 'C')">&darr;</button>
        <button class="btn remote-button" aria-label="Right" onclick="buttonClicked(this, 'D')">&rarr;</button>
        <button class="btn remote-button" onclick="buttonClicked(this, '7')">7</button>
        <button class="btn remote-button" onclick="buttonClicked(this, '8')">8</button>
        <button class="btn remote-button" onclick="buttonClicked(this, '9')">9</button>
        <button class="btn remote-button" aria-label="Plus" onclick="buttonClicked(this, 'UP')">+</button>
        <button class="btn remote-button" onclick="buttonClicked(this, '4')">4</button>
        <button class="btn remote-button" onclick="buttonClicked(this, '5')">5</button>
        <button class="btn remote-button" onclick="buttonClicked(this, '6')">6</button>
        <button class="btn remote-button" aria-label="Minus" onclick="buttonClicked(this, 'DN')">-</button>
        <button class="btn remote-button" onclick="buttonClicked(this, '1')">1</button>
        <button class="btn remote-button" onclick="buttonClicked(this, '2')">2</button>
        <button class="btn remote-button" onclick="buttonClicked(this, '3')">3</button>
        <button class="btn remote-button" aria-label="Square" onclick="buttonClicked(this, 'SQUARE')">&#9632;</button>
        <button class="btn remote-button remote-modifier" id="altButton" onclick="buttonPressed(this)">Ent+</button>
        <button class="btn remote-button" onclick="buttonClicked(this, '0')">0</button>
        <button class="btn remote-button remote-modifier" id="longButton" onclick="buttonPressed(this)">Long</button>
    </div>
</div>
<script>
function fetchImage() {
    const imageElement = document.getElementById('image');
    fetch("/image?t=" + new Date().getTime())
        .then(response => {
            if (!response.ok) { throw Error(response.statusText); }
            return response.blob();
        })
        .then(imageBlob => {
            let imageObjectURL = URL.createObjectURL(imageBlob);
            imageElement.src = imageObjectURL;
            // When the image can't be fetched, display a static message
            const errorElement = document.getElementById('error');
            errorElement.innerHTML = "";
        })
        .catch(error => {
            console.log(error);
            // When the image can't be fetched, display a static message
            const errorElement = document.getElementById('error');
            errorElement.innerHTML = "PiFinder server is currently unavailable. Please try again later.";
        })
        .finally(() => {
            // Schedule the next fetch operation after 100 milliseconds, whether this operation was successful or not
            setTimeout(fetchImage, 100);
        });
}

// Start the first fetch operation
fetchImage();

function buttonPressed(btn) {
    const altButton = document.getElementById("altButton");
    const longButton = document.getElementById("longButton");

    // If the other button is pressed, unpress it
    if (btn === altButton && longButton.classList.contains('pressed')) {
        longButton.classList.remove('pressed');
    } else if (btn === longButton && altButton.classList.contains('pressed')) {
        altButton.classList.remove('pressed');
    }

    // If this button is already pressed, unpress it; otherwise, press it
    if (btn.classList.contains('pressed')) {
        btn.classList.remove('pressed');
    } else {
        btn.classList.add('pressed');
    }
}

function buttonClicked(btn, code) {
    const altButton = document.getElementById("altButton");
    const longButton = document.getElementById("longButton");

    if (altButton.classList.contains('pressed')) {
        code = `ALT_${code}`;
        altButton.classList.remove('pressed');
    } else if (longButton.classList.contains('pressed')) {
        code = `LNG_${code}`;
        longButton.classList.remove('pressed');
    }

    fetch('/key_callback', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ button: code }),
    })
    .then(response => response.json())
    .then(data => console.log(data))
    .catch((error) => {
        console.error('Error:', error);
    });
}
</script>

% if not defined("embedded") or not embedded:
%   include("footer.tpl", title="PiFinder UI")
% else:
  </main>
</body>
</html>
% end
