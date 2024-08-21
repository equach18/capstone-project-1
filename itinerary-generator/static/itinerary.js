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
const BASE_URL = "http://127.0.0.1:5000/";

$(document).ready(function () {
  // Create an event listener on the Google picker to convert the user's input to the formatted address.
  $("gmpx-place-picker").on("gmpx-placechange", function (e) {
    let place = e.target.value;
    $("#location").val(place?.formattedAddress ?? "");
  });

  //   Retrieves the user's selected category inputs and puts it into a list
  async function getCatInputs(e) {
    e.preventDefault();
    let count = parseInt($activityCount.val());
    let selectedCats = [];

    // obtain the itinerary id
    const pathParts = window.location.pathname.split("/");
    for (let i = 1; i <= count; i++) {
      let selectedValue = $(`#activity${i}`).val();
      //   add the value to the array if it is selected
      if (selectedValue) {
        selectedCats.push(selectedValue);
      }
    }
    try {
      // Send the selected categories to the server via a POST request
      const resp = await axios.post(
        `${BASE_URL}/itinerary/${pathParts[2]}/new`,
        { categories: selectedCats }
      );
      // Redirect to the itinerary once it is added
      window.location.href = resp.data.redirect_url;
    } catch (error) {
      //Console error message if and error with selecting the errors occur
      console.error("Error submitting the selected categories:", error);
    }
  }

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
    let count = parseInt($activityCount.val());
    renderActivityInputs(count);
  });

  // event listener for activitity input form
  const $activityForm = $("#activity-form");
  $activityForm.on("submit", getCatInputs);
});
