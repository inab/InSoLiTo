// ------------------------------------------------------------ IMPORTS ------------------------------------------------------------ //

// Dependencies
import $ from "jquery";
import "jquery-ui/ui/core";
import "jquery-ui/ui/widgets/slider.js";
import "jquery-ui/ui/widgets/autocomplete.js";

// Style
import "jquery-ui/themes/base/theme.css";
import "jquery-ui/themes/base/slider.css";
import "vis-network/dist/dist/vis-network.min.css";
import "./styles/extras.scss";
import "./styles/style.css";
import * as bootstrap from 'bootstrap'

// JSON
import OccurData from "../../DB/RelationshipSliderData.json";
import YearData from "../../DB/YearSliderData.json";
import ToolTopicData from "../../DB/ToolTopicAutocomplete.json";
import sampleConfig from "./config.json";

// Images
import ToolImage from "./images/tool_centered_sm.png";
import DatabaseImage from "./images/database_centered_sm.png";
import TopicImage from "./images/topic_centered_sm.png";
import logoInSoLiTo from "./images/logo_InSoLiTo.png";

// Modules
import { actionSidebar, Barchart, sliderRangeFunction, addLegend, initAutocomplete, removeAllTopicsMenu } from "./modules.js/navBar";
import { Vis, drawVis, updateNodes, clusterMode, addNodes, reset } from "./modules.js/graph";



// ------------------------------------------------------------ VARIABLES ------------------------------------------------------------ //

// Select the canvas element with the ID "YearCanvas" from the DOM.
let YearCanvas = $("#YearCanvas")[0];

// Create a new instance of the Barchart class for the yearly bar chart (YearBarchart).
let YearBarchart = new Barchart({
  canvas: YearCanvas, // The canvas element where the chart will be drawn.
  padding: 0, // Padding inside the chart, set to 0 in this case.
  data: YearData, // The data array to be visualized in the bar chart.
  colors: ["#0b579f"], // Array of colors for the bars, using a single color here.
});

// Select the canvas element with the ID "OccurCanvas" from the DOM.
let OccurCanvas = $("#OccurCanvas")[0];

// Create a new instance of the Barchart class for the occurrence bar chart (OccurBarchart).
let OccurBarchart = new Barchart({
  canvas: OccurCanvas, // The canvas element where the chart will be drawn.
  padding: 0, // Padding inside the chart, set to 0 in this case.
  data: OccurData, // The data array to be visualized in the bar chart.
  colors: ["#0b579f"], // Array of colors for the bars, using a single color here.
});

// Select the alert element with the ID "liveAlertPlaceholder" from the DOM.
const alertPlaceholder = document.getElementById('liveAlertPlaceholder')



// ------------------------------------------------------------ FUNCTIONS ------------------------------------------------------------ //

// ------------------------------ Function-1 ------------------------------
/**
 * Removes the loading page after the graph has been drawn
 */
function removeLoadingPage() {
  // Get the loading page element
  const loadingPage = $("#enter-webpage");
  if (!loadingPage || loadingPage.length === 0) {
    throw new Error("Loading page not found");
  }
  try {
    // Remove the loading page element
    loadingPage.remove();
  } catch (error) {
    console.log("Error in removeLoadingPage:", error.message);
  }
}



// ------------------------------ Function-2 ------------------------------
/**
 * Creates the home page content.
 * This function creates a div element and appends an img element with the InSoLiTo logo.
 * It then prepends the div element to the initial screen element.
 *
 * @throws Will throw an error if the home page element or img element cannot be created.
 * @throws Will throw an error if the home page element cannot be found in the DOM.
 */
function createHomePage() {
  // Get the initial screen element where the home page content will be added
  let homePage = $("#inital-screen");
  if (!homePage || homePage.length === 0) {
    throw new Error("Home page not found");
  }
  // Create a new div element to hold the home page content
  let divHomePage = $("<div></div>");
  // Create an img element for the InSoLiTo logo
  let imgHomePage = $('<img>', {
    class: "imgHomePage", // CSS class for styling
    alt: "InSoLiTo Logo", // Alt text for accessibility
    src: logoInSoLiTo // Source of the logo image
  });
  if (!imgHomePage) {
    throw new Error("imgHomePage is null");
  }
  // Append the logo image to the div element
  divHomePage.append(imgHomePage);
  try {
    // Prepend the div element to the initial screen element
    homePage.prepend(divHomePage);
  } catch (error) {
    console.log("Error in createHomePage:", error.message);
  }
}



// ------------------------------ Function-3 ------------------------------
/**
 * Appends a new alert to the page.
 * @param {string} message The text message to be displayed in the alert.
 * @param {string} type The type of alert. It can be "success", "info", "warning", "danger", or "primary".
 */
function appendAlert (message, type) {
  // Create a div element to hold the alert
  const wrapper = document.createElement('div')
  // Generate the HTML for the alert
  wrapper.innerHTML = [
    `<div class="alert alert-${type} alert-dismissible" role="alert">`,
    // The message to be displayed in the alert
    `   <div>${message}</div>`,
    // The close button
    '   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
    '</div>'
  ].join('')

  // Append the alert to the alert placeholder
  alertPlaceholder.append(wrapper)
}



// ------------------------------ Function-4 ------------------------------
/**
 * Toggles the visibility of the topics added element.
 * If the element is visible, it will be hidden and vice versa.
 */
function toggleTopicsAdded() {
  // Get the element with the ID "topics-toggle-visibility"
  let topicsAdded = $("#topics-toggle-visibility");
  if (!topicsAdded || topicsAdded.length === 0) {
    throw new Error("Topics added element not found");
  }
  // Try to hide or show the element
  try {
    // Toggle the visibility of the element
    topicsAdded.toggleClass("hidden");
  } catch (error) {
    // TODO Handle the error
    console.log("Error in toggleTopicsAdded:", error.message);
  }
}



// ------------------------------ Function-5 ------------------------------
/**
 * Toggles the visibility of the tools added element.
 * If the element is visible, it will be hidden and vice versa.
 */
function toggleToolsAdded() {
  // Get the element with the ID "tools-toggle-visibility"
  let toolsAdded = $("#tools-toggle-visibility");
  if (!toolsAdded || toolsAdded.length === 0) {
    throw new Error("Tools added element not found");
  }
  try {
    // Toggle the visibility of the element
    toolsAdded.toggleClass("hidden");
  } catch (error) {
    // TODO Handle the error
    console.log("Error in toggleToolsAdded:", error.message);
  }
}



// ------------------------------ Function-6 ------------------------------
function toggleLegend() {
  // Get the element with the ID "legend"
  let legend = $("#legend");
  if (!legend || legend.length === 0) {
    throw new Error("Legend element not found");
  }
  try {
    // Toggle the visibility of the element
    legend.toggleClass("hidden");
  } catch (error) {
    // TODO Handle the error
    console.log("Error in toggleLegend:", error.message);
  }
}



// ------------------------------------------------------------ RUNTIME ------------------------------------------------------------ //

// Attach a click event handler to the element with the ID "openbtn".
// When clicked, it calls the function `actionSidebar` to toggle or manage the sidebar.
$("#openbtn").on("click", () => {
  actionSidebar();
});

try {
  // Execute the following functions once the DOM is fully loaded.
  $(function () {
    createHomePage(); // Initializes or creates the homepage content.
    removeLoadingPage(); // Removes the loading page or spinner.
    drawVis(); // Draws visualizations, such as graphs or charts.
    actionSidebar(); // Toggles or manages the sidebar visibility.
    sliderRangeFunction(); // Sets up the slider range functionality.
    // Initializes autocomplete functionality with provided data and callbacks.
    initAutocomplete(ToolTopicData, addNodes, ToolImage, DatabaseImage, TopicImage);
    toggleTopicsAdded();
    toggleToolsAdded();
    toggleLegend();
  });

  // Draw the bar charts for YearBarchart and OccurBarchart.
  YearBarchart.draw();
  OccurBarchart.draw();

  // Attach a change event handler to radio buttons with the name "cluster_mode".
  // Executes when the cluster mode is changed.
  $("input[type=radio][name=cluster_mode]").change(function () {
    clusterMode();
    addLegend();
  });

  // Attach a change event handler to checkboxes with the name "displayArticles".
  // Executes when the display options for articles are toggled.
  $("input[type=checkbox][name=displayArticles]").change(function () {
    updateNodes();
  });

  // Attach a change event handler to elements with the IDs "allYearsEdges" and "EdgesByYear".
  // Executes when the edge type options are toggled.
  $("#allYearsEdges, #EdgesByYear").change(function () {
    updateNodes();
    // Get the selected edge type option.
    let optionEdges = $("input[name=typeOfEdges]:checked");
    // Hide or show the year column based on the selected edge type.
    if (optionEdges.val() === "allYearsEdges") {
      if ($("#yearColumn").hasClass("disp-block")) {
        $("#yearColumn").removeClass("disp-block");
      }
      $("#yearColumn").addClass("hidden");
    } else {
      // Show year column if "EdgesByYear" is selected.
      if ($("#yearColumn").hasClass("hidden")) {
        $("#yearColumn").removeClass("hidden");
      }
      $("#yearColumn").addClass("disp-block");
    }
  });

  // Attach a click event handler to the element with the ID "reset".
  // Executes when the reset button is clicked.
  $("#reset").on("click", function () {
    removeAllTopicsMenu();
    reset();
  });

  // Attach a click event handler to the element with the ID "stabilize".
  // Executes when the stabilize button is clicked.
  $("#stabilize").on("click", () => {
    Vis.stopSimulation();
  });

} catch (error) {
  console.log("Error in main:", error.message);
  // TODO change the alert link
  appendAlert("An error has occurred! Please try again and if the problem persists try again in a few minutes. <a href='#' class='alert-link'>Go back to home</a>.", "danger");
}



// ------------------------------------------------------------ EXPORTS ------------------------------------------------------------ //

export { appendAlert, toggleTopicsAdded, toggleToolsAdded, toggleLegend };