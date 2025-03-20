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

// Select the alert element with the ID "liveAlertPlaceholder" from the DOM.
const alertPlaceholder = $('#liveAlertPlaceholder');

// Select all elements with the data-bs-toggle attribute set to "tooltip"
const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');

const observer = new MutationObserver(() => toggleButtons());
observer.observe($("#VisNetwork")[0], { attributes: true, attributeFilter: ["class"] });



// ------------------------------------------------------------ FUNCTIONS ------------------------------------------------------------ //

// ------------------------------ Function-1 ------------------------------
/**
 * Removes the loading page after the graph has been drawn
 */
const removeLoadingPage = () => {
  // Get the loading page element
  const loadingPage = $("#enter-webpage");
  if (!loadingPage || loadingPage.length === 0) {
    throw new Error("Loading page not found");
  }
  try {
    // Remove the loading page element
    loadingPage.remove();
  } catch (error) {
    console.log(`Error in removeLoadingPage:${error.message}`);
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
const createHomePage = () => {
  // Get the initial screen element where the home page content will be added
  let homePage = $("#initial-screen");
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
    console.log(`Error in createHomePage: ${error.message}`);
  }
}



// ------------------------------ Function-3 ------------------------------
/**
 * Appends an alert message to the alert placeholder element.
 * @param {string} message The message to be displayed in the alert.
 * @param {string} type The type of alert to be displayed. Can be "success", "info", "warning", "danger".
 */
const appendAlert = (message, type) => {
  const wrapper = $('<div>').addClass(`alert alert-${type} alert-dismissible`)
    .attr('role', 'alert');

  const messageDiv = $('<div>').html(message);
  const actionButton = $('<button>')
    .addClass(`btn btn-outline-${type} btn-sm m-2`)
    .text('Go Home')
    .on('click', () => {
      removeAllTopicsMenu();
      reset();
      if ($("#initial-screen").hasClass("hidden")) {
        $("#initial-screen").removeClass("hidden");
      }
      $("#liveAlertPlaceholder").empty();
    });

  const closeButton = $('<button>')
    .addClass('btn-close')
    .attr({
      'type': 'button',
      'data-bs-dismiss': 'alert',
      'aria-label': 'Close'
    });

  messageDiv.append(actionButton);
  wrapper.append(messageDiv, closeButton);
  alertPlaceholder.append(wrapper);
};



// ------------------------------ Function-4 ------------------------------
/**
 * Shows the topics added element.
 *
 * This function removes the "hidden" class from the element with the ID 
 * "topics-toggle-visibility" to make it visible on the page.
 */
function showTopicsAdded() {
  // Get the element with the ID "topics-toggle-visibility"
  let topicsAdded = $("#topics-toggle-visibility");
  // Try to show the element
  try {
    // Remove the "hidden" class to make the element visible
    topicsAdded.removeClass("hidden");
  } catch (error) {
    // Log an error message if something goes wrong
    console.log("Error in showTopicsAdded:", error.message);
  }
}



// ------------------------------ Function-5 ------------------------------
/**
 * Hides the topics added element.
 *
 * This function adds the "hidden" class to the element with the ID
 * "topics-toggle-visibility" to make it invisible on the page.
 */
function hideTopicsAdded() {
  // Get the element with the ID "topics-toggle-visibility"
  const topicsAdded = $("#topics-toggle-visibility");
  // Try to hide or show the element
  try {
    // Add the "hidden" class to make the element invisible
    topicsAdded.addClass("hidden");
  } catch (error) {
    // Log an error message if something goes wrong
    console.log("Error in hideTopicsAdded:", error.message);
  }
}



// ------------------------------ Function-6 ------------------------------
/**
 * Shows the tools added element.
 *
 * This function removes the "hidden" class from the element with the ID 
 * "tools-toggle-visibility" to make it visible on the page.
 */
function showToolsAdded() {
  // Get the element with the ID "tools-toggle-visibility"
  let toolsAdded = $("#tools-toggle-visibility");
  // Try to show the element
  try {
    // Remove the "hidden" class to make the element visible
    toolsAdded.removeClass("hidden");
  } catch (error) {
    // Log an error message if something goes wrong
    console.log("Error in showToolsAdded:", error.message);
  }
}



// ------------------------------ Function-7 ------------------------------
/**
 * Hides the tools added element.
 *
 * This function adds the "hidden" class to the element with the ID
 * "tools-toggle-visibility" to make it invisible on the page.
 */
function hideToolsAdded() {
  // Get the element with the ID "tools-toggle-visibility"
  let toolsAdded = $("#tools-toggle-visibility");
  try {
    // Add the "hidden" class to make the element invisible
    toolsAdded.addClass("hidden");
  } catch (error) {
    // Log an error message if something goes wrong
    console.log("Error in hideToolsAdded:", error.message);
  }
}



// ------------------------------ Function-8 ------------------------------
/**
 * Shows the legend element.
 *
 * This function removes the "hidden" class from the element with the ID
 * "legend" to make it visible on the page.
 */
function showLegend() {
  // Get the element with the ID "legend"
  let legend = $("#legend");
  // Try to show the element
  try {
    // Remove the "hidden" class to make the element visible
    legend.removeClass("hidden");
  } catch (error) {
    // Log an error message if something goes wrong
    console.log("Error in showLegend:", error.message);
  }
}



// ------------------------------ Function-9 ------------------------------
/**
 * Hides the legend element.
 *
 * This function adds the "hidden" class to the element with the ID
 * "legend" to make it invisible on the page.
 */
function hideLegend() {
  // Get the element with the ID "legend"
  let legend = $("#legend");
  try {
    // Add the "hidden" class to make the element invisible
    legend.addClass("hidden");
  } catch (error) {
    // TODO Handle the error
    console.log("Error in hideLegend:", error.message);
  }
}



// ------------------------------ Function-10 ------------------------------
/**
 * Initializes Bootstrap tooltips for all elements with the data attribute 
 * 'data-bs-toggle' set to 'tooltip'.
 * 
 * This function iterates over the list of elements with tooltips and creates 
 * a Bootstrap Tooltip instance for each element, enabling the tooltip 
 * functionality.
 */
function initializeTooltips() {
  // Loop over each element that should have a tooltip
  tooltipTriggerList.forEach(function (tooltipTriggerEl) {
    // Initialize a new Bootstrap Tooltip instance for the element
    new bootstrap.Tooltip(tooltipTriggerEl);
  });
}



// ------------------------------ Function-11 ------------------------------
/**
 * Toggles the state of the buttons with the IDs "reset" and "stabilize"
 * depending on whether the element with the ID "VisNetwork" has the class
 * "hidden" or not.
 *
 * If the element with the ID "VisNetwork" has the class "hidden", the
 * buttons are disabled, meaning they cannot be clicked. If the element
 * does not have the class "hidden", the buttons are enabled.
 */
const toggleButtons = () => {
  if ($("#VisNetwork").hasClass("hidden")) {
    // Disable the buttons
    $("#reset").prop("disabled", true);
    $("#stabilize").prop("disabled", true);
  } else {
    // Enable the buttons
    $("#reset").prop("disabled", false);
    $("#stabilize").prop("disabled", false);
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
  $(() => {
    createHomePage(); // Initializes or creates the homepage content.
    removeLoadingPage(); // Removes the loading page or spinner.
    drawVis(); // Draws visualizations, such as graphs or charts.
    actionSidebar(); // Toggles or manages the sidebar visibility.
    sliderRangeFunction(); // Sets up the slider range functionality.
    // Initializes autocomplete functionality with provided data and callbacks.
    initAutocomplete(ToolTopicData, addNodes, ToolImage, DatabaseImage, TopicImage);
    hideTopicsAdded();
    hideToolsAdded();
    hideLegend();
    initializeTooltips();
    toggleButtons();
  });

  // Draw the bar charts for YearBarchart and OccurBarchart.
  YearBarchart.draw();

  // Attach a change event handler to radio buttons with the name "cluster_mode".
  // Executes when the cluster mode is changed.
  $("input[type=radio][name=cluster_mode]").change(() => {
    clusterMode();
    addLegend();
  });

  // Attach a change event handler to checkboxes with the name "displayArticles".
  // Executes when the display options for articles are toggled.
  $("input[type=checkbox][name=displayArticles]").change(() => {
    updateNodes();
  });

  // Attach a change event handler to elements with the IDs "allYearsEdges" and "EdgesByYear".
  // Executes when the edge type options are toggled.
  $("#allYearsEdges, #EdgesByYear").change(() => {
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
  $("#reset").on("click", () => {
    if ($("#reset").prop("disabled")) return;
    removeAllTopicsMenu();
    reset();
    $("#initial-screen").addClass("hidden");
    $("#VisNetwork").addClass("hidden");
    $("#resetPage").removeClass("hidden");
  });

  // Attach a click event handler to the element with the ID "stabilize".
  // Executes when the stabilize button is clicked.
  $("#stabilize").on("click", () => {
    Vis.stopSimulation();
  });

} catch (error) {
  console.log(`Error in main: ${error.message}`);
  // TODO change the alert link
  appendAlert("An error has occurred! Please try again and if the problem persists try again in a few minutes.", "danger");
}



// ------------------------------------------------------------ EXPORTS ------------------------------------------------------------ //

export { appendAlert, showTopicsAdded, hideTopicsAdded, showToolsAdded, hideToolsAdded, showLegend, hideLegend };