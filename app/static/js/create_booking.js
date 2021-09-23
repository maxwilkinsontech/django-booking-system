var dateInput = document.getElementById('id_date');
var partyInput = document.getElementById('id_party');
var partyDiv = document.getElementById('party_div');
var timeInput; // Populated when time's html loaded.
var timeDiv = document.getElementById('time_div');
var clientElements = document.getElementById('client_elements');

// STEP 1: Select a date
dateInput.onchange = (e) => step1();
// STEP 2: Select the party size
partyInput.onchange = (e) => step2();
// STEP 3: Select the time - This step is done when the party size is selected and 
//         and the html select widget loads.

function step1() {
    let bookingDate = dateInput.value;
    // If value added, shown party input, else hide it and all other inputs.
    if (!bookingDate.trim().length) {
        partyDiv.style.display = 'none';
        timeDiv.style.display = 'none';
        clientElements.style.display = 'none';
    } else {
        partyDiv.style.display = 'block';
        timeDiv.style.display = 'none';
        clientElements.style.display = 'none';
        // Remove party and time input values (may have values already).
        partyInput.value = '';
        if (timeInput != null) timeInput.value = '';
    }
}

function step2() {
    let partySize = partyInput.value;
    if (partySize != null || partySize != '') {
        timeDiv.style.display = 'block';
        clientElements.style.display = 'none';
        // Remove time input value (may have a value already).
        if (timeInput != null) timeInput.value = '';

        let url = `${getTimesURL}?date=${dateInput.value}&party_size=${partySize}`;
        if (frontend) {
            url += '&f=true'
        }

        timeDiv.innerHTML = 'Loading times...';

        fetch(url).then(function (response) {
            return response.text();
        }).then(function (html) {
            timeDiv.innerHTML = html;
        }).then(function () {
            timeInput = document.getElementById('id_time');
            timeInput.onchange = (e) => step3();
        });
    }
}

function step3() {
    let time = timeInput.value;
    if (time != null || time != '') {
        clientElements.style.display = 'block';
    }
}