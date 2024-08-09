$(document).ready(function() {
    const $picker = $('gmpx-place-picker');
    const $locationInput = $('#location');

    $picker.on('gmpx-placechange', function(e) {
        $locationInput.val(e.target.value?.formattedAddress ?? '');
    });
});