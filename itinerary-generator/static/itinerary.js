// Categories for the activities
ACTIVITY_CAT = [
  "Random",
  "Food",
  "Hiking",
  "Tours",
  "Shopping",
  "Adventure",
  "Outdoors",
];

$(document).ready(function () {
  // Create an event listener on the Google picker to convert the user's input to the formatted address.
  $("gmpx-place-picker").on("gmpx-placechange", function (e) {
    $("#location").val(e.target.value?.formattedAddress ?? "");
  });

  // Renders the activity input fields depending on the the count chosen in the add activities page
  function renderActivityInputs(count) {
    const $activityInputContainer = $("#activity-input-container");

    // clear the container if any
    $activityInputContainer.empty();

    for (let i = 1; i <= count; i++) {
      // create the elements to add to the form
      let $div = $("<div>", { class: "form-group" });

      let $label = $("<label>", {
        for: `activity${i}`,
        text: `Activity ${i}`,
      });

      let $select = $("<select>", {
        class: "form-control",
        id: `activity${i}`,
        name: `activity${i}`,
      });

      //add each category for the options
      $select.append($("<option>", { value: "", text: "Choose a Category!" }));
      ACTIVITY_CAT.forEach(function (option) {
        $select.append($("<option>", { value: option, text: option }));
      });

      $div.append($label).append($select);
      $activityInputContainer.append($div);
    }
  }

  //add an event listener for any change in activity count.
  const $activityCount = $("#activity-count");

  $activityCount.change(function () {
    const count = parseInt($activityCount.val());
    renderActivityInputs(count);
  });
});
