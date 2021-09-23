function initFlatpickr(futureOnly = false, minDate = null, maxDate = null) {
    // Initilise date input widget.
    var config = {
        dateFormat: "Y-m-d",
    }

    if (minDate != null) {
        config['minDate'] = minDate;
    } else if (futureOnly) {
        config['minDate'] = "today";
    }
    if (maxDate != null) {
        config['maxDate'] = maxDate;
    }

    flatpickr('.flatpickrDateField', config);
}

function initTimepickr() {
    // Initialise time input widget.
    var config = {
        enableTime: true,
        noCalendar: true,
        dateFormat: "H:i",
        time_24hr: true,
        minuteIncrement: 15,
    }

    flatpickr('.flatpickrTimeField', config);
}