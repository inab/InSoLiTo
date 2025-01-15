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
 * Creates the home page by adding the InSoLiTo logo to the initial screen.
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
  // TODO issue #11
}
