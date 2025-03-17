// ------------------------------------------------------------ IMPORTS ------------------------------------------------------------ //

// Dependencies
import $ from "jquery";
import "jquery-ui/ui/core";
import "jquery-ui/ui/widgets/slider.js";
import "jquery-ui/ui/widgets/autocomplete.js";

// JSON
import OccurData from "../../../DB/RelationshipSliderData.json";
import YearData from "../../../DB/YearSliderData.json";

// Images
import CloseButton from "../images/xmark-solid.svg";
// import MenuButton from "../images/bars-solid.svg";
import MenuOpen from "../images/arrow_menu_open.svg";
import MenuClose from "../images/arrow_menu_close.svg";
import ToolImage from "../images/tool_centered_sm.png";
import DatabaseImage from "../images/database_centered_sm.png";
import PaperImage from "../images/paper_centered_sm.png";

// Modules
import { returnClusters, updateNodes } from "./graph";
import { appendAlert, showLegend, hideLegend } from "../main";



// ------------------------------------------------------------ FUNCTIONS ------------------------------------------------------------ //

// ------------------------------ Function-1 ------------------------------
/**
 * This function is used to open and close the sidebar menu.
 * When the menu is opened, the width of the sidebar is set to 300px and the width of the main content is set to 100% - 300px.
 * When the menu is closed, the width of the sidebar is set to 0 and the width of the main content is set to 100%.
 */
const actionSidebar = () => {
  try {
    // Remove the previous menu image if it exists
    let menuImage = $("#MenuImage");
    if (menuImage.length > 0) {
      menuImage.remove();
    }
    // Get the main content and button elements
    let main = $("#main");
    if (!main || main.length === 0) {
      throw new Error("Main element not found");
    }
    let button = $("#openbtn");
    if (!button || button.length === 0) {
      throw new Error("Open button not found");
    }
    // Create a new image element for the button
    let buttonImage = $('<img id="MenuImage" alt="">');
    if (!buttonImage) {
      throw new Error("Failed to create MenuImage element");
    }
    // Check the current state of the sidebar and toggle it
    if (main.css('marginLeft') === "0px" || !main.css('marginLeft')) {
      // Open the sidebar
      if ($("#mySidebar").hasClass("sidebar-closed")) {
        $("#mySidebar").removeClass("sidebar-closed");
      }
      $("#mySidebar").addClass("sidebar-open");
      if (main.hasClass("main-without-sidebar")) {
        main.removeClass("main-without-sidebar");
      }
      main.addClass("main-with-sidebar");
      buttonImage.attr('src', MenuClose); // Set to close button image
      if ($("#visualization").hasClass("visualization-without-sidebar")) {
        $("#visualization").removeClass("visualization-without-sidebar");
      }
      $("#visualization").addClass("visualization-with-sidebar");
      if (!$("#openbtn").hasClass("sidebar-open")) {
        $("#openbtn").addClass("sidebar-open");
      }
    } else {
      // Close the sidebar
      if ($("#mySidebar").hasClass("sidebar-open")) {
        $("#mySidebar").removeClass("sidebar-open");
      }
      $("#mySidebar").addClass("sidebar-closed");
      if (main.hasClass("main-with-sidebar")) {
        main.removeClass("main-with-sidebar");
      }
      main.addClass("main-without-sidebar");
      buttonImage.attr('src', MenuOpen); // Set to menu button image
      if ($("#visualization").hasClass("visualization-with-sidebar")) {
        $("#visualization").removeClass("visualization-with-sidebar");
      }
      $("#visualization").addClass("visualization-without-sidebar");
      if ($("#openbtn").hasClass("sidebar-open")) {
        $("#openbtn").removeClass("sidebar-open");
      }
    }
    // Add the new image to the button
    button.append(buttonImage);
  } catch (error) {
    console.error(`Error in actionSidebar: ${error.message}`);
    // TODO change the alert link
    appendAlert('While loading the sidebar, an error occurred. Please refresh the page.', 'danger')
  }
}



// ------------------------------ Function-2 ------------------------------
/**
 * This function draws a line on the canvas.
 * @param {Object} ctx - The canvas context.
 * @param {Number} startX - The x coordinate of the start of the line.
 * @param {Number} startY - The y coordinate of the start of the line.
 * @param {Number} endX - The x coordinate of the end of the line.
 * @param {Number} endY - The y coordinate of the end of the line.
 * @param {String} color - The color of the line.
 */
const drawLine = (ctx, startX, startY, endX, endY, color) => {
  if (!ctx) {
    throw new Error("drawLine: ctx is null");
  }
  if (typeof startX !== "number" || typeof startY !== "number" || typeof endX !== "number" || typeof endY !== "number") {
    throw new Error("drawLine: start or end coordinates are not numbers");
  }
  // Save the current state of the canvas
  ctx.save();
  try {
    // Set the color of the line
    ctx.strokeStyle = color;
    // Start drawing the line
    ctx.beginPath();
    // Move to the start of the line
    ctx.moveTo(startX, startY);
    // Draw the line to the end of the line
    ctx.lineTo(endX, endY);
    // Draw the line
    ctx.stroke();
  } finally {
    // Restore the previous state of the canvas
    ctx.restore();
  }
}



// ------------------------------ Function-3 ------------------------------
/**
 * This function draws a bar on the canvas.
 * @param {Object} ctx - The canvas context.
 * @param {Number} upperLeftCornerX - The x coordinate of the upper left corner of the bar.
 * @param {Number} upperLeftCornerY - The y coordinate of the upper left corner of the bar.
 * @param {Number} width - The width of the bar.
 * @param {Number} height - The height of the bar.
 * @param {String} color - The color of the bar.
 */
const drawBar = (ctx, upperLeftCornerX, upperLeftCornerY, width, height, color) => {
  if (!ctx) {
    throw new Error("drawBar: ctx is null or undefined");
  }
  if (typeof upperLeftCornerX !== "number" || typeof upperLeftCornerY !== "number" ||
    typeof width !== "number" || typeof height !== "number") {
    throw new Error("drawBar: coordinates and dimensions must be numbers");
  }
  // Save the current state of the canvas
  ctx.save();
  try {
    // Set the color of the bar
    ctx.fillStyle = color;
    // Draw the bar
    ctx.fillRect(upperLeftCornerX, upperLeftCornerY, width, height);
  } finally {
    // Restore the previous state of the canvas
    ctx.restore();
  }
}



// ------------------------------ Function-4 ------------------------------
/**
 * This function creates a bar chart on a canvas.
 * @param {Object} options - The options for the bar chart.
 * @param {Object} options.canvas - The canvas element to draw the bar chart on.
 * @param {Object} options.data - The data to draw the bar chart for.
 * @param {Object} options.colors - The colors to use for the bars.
 * @param {Number} options.padding - The padding to leave around the bar chart.
 * @param {Number} options.gridScale - The scale of the grid lines.
 * @param {String} options.gridColor - The color of the grid lines.
 */
let Barchart = function (options) {
  if (!options || !options.canvas || !options.data || !options.colors) {
    throw new Error("Barchart: options must have canvas, data, and colors");
  }
  this.options = options;
  this.canvas = options.canvas;
  if (!this.canvas) {
    throw new Error("Barchart: canvas is null or undefined");
  }
  this.ctx = this.canvas.getContext("2d");
  if (!this.ctx) {
    throw new Error("Barchart: canvas is not a HTMLCanvasElement");
  }
  this.colors = options.colors;
  // Function that draws the bar chart on the canvas.
  this.draw = () => {
    // Find the maximum value in the data
    let maxValue = 0;
    for (let categ in this.options.data) {
      maxValue = Math.max(maxValue, this.options.data[categ]);
    }
    if (maxValue === 0) {
      throw new Error("Barchart: All values in data are zero");
    }
    // Calculate the actual height and width of the canvas
    let canvasActualHeight = this.canvas.height - this.options.padding * 2;
    let canvasActualWidth = this.canvas.width - this.options.padding * 2;
    // Draw the grid lines
    let gridValue = 0;
    while (gridValue <= maxValue) {
      let gridY =
        canvasActualHeight * (1 - gridValue / maxValue) + this.options.padding;
      drawLine(
        this.ctx,
        0,
        gridY,
        this.canvas.width,
        gridY,
        this.options.gridColor
      );
      this.ctx.save();
      this.ctx.fillStyle = this.options.gridColor;
      this.ctx.restore();
      gridValue += this.options.gridScale;
    }
    // Draw the bars
    let barIndex = 0;
    let numberOfBars = Object.keys(this.options.data).length;
    if (numberOfBars === 0) {
      throw new Error("Barchart: data is empty");
    }
    let barSize = canvasActualWidth / numberOfBars;
    for (let categ in this.options.data) {
      let val = this.options.data[categ];
      if (isNaN(val) || val < 0) {
        throw new Error("Barchart: value in data is not a positive number");
      }
      let barHeight = Math.round((canvasActualHeight * val) / maxValue);
      drawBar(
        this.ctx,
        this.options.padding + barIndex * barSize,
        this.canvas.height - barHeight - this.options.padding,
        barSize,
        barHeight,
        this.colors[barIndex % this.colors.length]
      );
      barIndex++;
    }
  };
};



// ------------------------------ Function-5 ------------------------------
/**
 * Converts a position on a slider (0 to 100) to the corresponding value
 * in OccurData, which is assumed to have values sorted in ascending order.
 *
 * @param {number} position - A number between 0 and 100 representing the position on the slider.
 * @returns {number} - The corresponding value from OccurData.
 * @throws {Error} - Throws an error if the position is not a number between 0 and 100, if OccurData is null or empty, or if calculated minv or maxv are not valid numbers.
 */
const logslider = (position) => {
  // Validate the position input
  if (typeof position !== "number" || position < 0 || position > 100) {
    throw new Error("logslider: position must be a number between 0 and 100");
  }
  // Define the minimum and maximum positions on the slider
  let minp = 0;
  let maxp = 100;

  // Check if OccurData is valid and has keys
  if (!OccurData || Object.keys(OccurData).length === 0) {
    throw new Error("logslider: OccurData is null or has no keys");
  }
  // Calculate the minimum and maximum logarithmic values from OccurData
  let minv = Math.log(parseInt(Object.keys(OccurData)[0]));
  let maxv = Math.log(parseInt(Object.keys(OccurData)[Object.keys(OccurData).length - 1]));

  // Validate the calculated logarithmic values
  if (isNaN(minv) || isNaN(maxv)) {
    throw new Error("logslider: minv or maxv are not valid numbers");
  }
  // Compute the scale for the logarithmic conversion
  let scale = (maxv - minv) / (maxp - minp);
  // Return the exponential value corresponding to the slider position
  return Math.trunc(Math.exp(minv + scale * (position - minp)));
}



// ------------------------------ Function-6 ------------------------------
/**
 * Initializes the two sliders for the range of years and the range of occurances.
 *
 * The first slider is for the range of years and the range of occurances.
 * The second slider is for the range of occurances.
 *
 * The function also initializes the text inputs for the two sliders.
 *
 * @throws {Error} If YearData or OccurData is not defined
 * @throws {Error} If YearData or OccurData is empty
 * @throws {Error} If the values in YearData or OccurData are not numbers
 */
const sliderRangeFunction = () => {
  // Validate YearData and OccurData
  if (!YearData || !OccurData) {
    throw new Error("YearData or OccurData is not defined");
  }
  // Validate YearData content
  const yearKeys = Object.keys(YearData);
  if (!yearKeys.length) {
    throw new Error("YearData is empty");
  }
  // Validate OccurData content
  const occurKeys = Object.keys(OccurData);
  if (!occurKeys.length) {
    throw new Error("OccurData is empty");
  }
  // The slider for the range of years
  $("#year-slider-range").slider({
    // The slider is a range slider
    range: true,
    // The minimum value of the slider is the first year in the YearData object
    min: parseInt(yearKeys[0]),
    // The maximum value of the slider is the last year in the YearData object
    max: parseInt(yearKeys[yearKeys.length - 1]),
    // The initial values of the slider are the first and last years in the YearData object
    values: [
      parseInt(yearKeys[0]),
      parseInt(yearKeys[yearKeys.length - 1]),
    ],
    // When the slider is changed, update the text input for the slider
    slide: (event, ui) => {
      // Update the text input for the slider
      $("#yearAmount").val(ui.values[0] + " - " + ui.values[1]);
    },
    // When the slider is changed, update the graph
    change: () => {
      // Update the graph
      updateNodes();
    },
    // When the slider is created, update the text input for the slider
    create: () => {
      // Update the text input for the slider
      $("#yearAmount").val(
        $("#year-slider-range").slider("values", 0) +
        " - " +
        $("#year-slider-range").slider("values", 1)
      );
    },
  });
  $("#occur-slider-range").slider({
    range: true,
    min: 0,
    max: 100,
    values: [1, 100],
    slide: (event, ui) => {
      // Update the text input for the slider
      $("#occurAmount").val(logslider(ui.values[0]));
      // Update the graph
      updateNodes();
    },
    change: () => {
      // Update the graph
      const minValue = logslider($("#occur-slider-range").slider("values", 0));
      updateNodes();
    },
    create: () => {
      // Update the text input for the slider
      const minValue = logslider($("#occur-slider-range").slider("values", 0));
      $("#occurAmount").val(minValue);
    },
  });
  // Disable the second handle of the second slider
  $("#occur-slider-range .ui-slider-handle:eq(1)").addClass("ui-state-disabled");
  $("#occur-slider-range .ui-slider-handle:eq(1)").css("visibility", "hidden");
}



// ------------------------------ Function-7 ------------------------------
/**
 * Initializes the autocomplete input field.
 *
 * The autocomplete input field is used to search for tools, databases, and topics.
 * It is initialized with a list of all available tools, databases, and topics.
 * When the user selects an item from the list, the corresponding node is added
 * to the graph.
 *
 * @param {Object} toolTopicData - A list of all available tools, databases, and topics.
 * @param {Function} addNodesFn - The function to call when the user selects an item from the list.
 * @param {string} toolImage - The image to use for tools.
 * @param {string} databaseImage - The image to use for databases.
 * @param {string} topicImage - The image to use for topics.
 */
const initAutocomplete = (toolTopicData, addNodesFn, toolImage, databaseImage, topicImage) => {
  if (!toolTopicData || !Array.isArray(toolTopicData)) {
    throw new Error("Invalid toolTopicData: must be a non-empty array");
  }
  if (typeof addNodesFn !== 'function') {
    throw new Error("Invalid addNodesFn: must be a function");
  }
  if (!toolImage || !databaseImage || !topicImage) {
    throw new Error("Invalid image sources: must not be null or undefined");
  }
  $("#tooltopic_autocomplete").autocomplete({
    // The source of the data for the autocomplete input field is the list of all available tools, databases, and topics.
    source: (request, response) => {
      let term = $.ui.autocomplete.escapeRegex(request.term);
      let matcher1 = new RegExp("^" + term, "i");
      let matcher2 = new RegExp("^.+" + term, "i");
      const subarray = (matcher) => {
        return $.grep(toolTopicData, (item) => {
          if (!item || typeof item.value !== 'string') {
            return false;
          }
          return matcher.test(item.value);
        });
      }
      // The list of available tools, databases, and topics is filtered based on the input provided by the user.
      let results = $.merge(subarray(matcher1), subarray(matcher2));
      if (results.length === 0) {
        results.push({ value: "No results found", labelnode: ["No results found"] });
      }
      response(results);
    },
    // The minimum length of the input required to trigger the autocomplete input field.
    minLength: 1,
    // The function to call when the user selects an item from the list.
    select: (event, ui) => {
      if (ui.item.value === "No results found") {
        return false;
      }
      let name = ui.item.value;
      let idNode = ui.item.idNodes;
      let labelNode = ui.item.labelnode;
      if (!name || !idNode || !labelNode) {
        throw new Error("Invalid selection: item properties cannot be null or undefined");
      }
      if (Array.isArray(labelNode)) {
        labelNode = labelNode[0];
      }
      // Add the selected node to the graph.
      addNodesFn(name, idNode, labelNode);
      // Clear the input field.
      $(this).val("");
      // Prevent the default action of the event.
      return false;
    },
    // Set the z-index of the autocomplete list to 1000 to ensure that it is displayed on top of other elements.
    open: () => {
      $(".ui-autocomplete").addClass("ui-autocomplete-zindex-1000");
    },
  }).autocomplete("instance")._renderItem = (ul, item) => {
    if (item.labelnode[0] === "No results found") {
      return $('<li>').append(`<div class="boxAutocomplete noResults">No results found</div>`).appendTo(ul);
    }

    if (item.labelnode[0] === "Tool") {
      // Create a list item for the autocomplete list.
      return $(`<li>
        <div class="boxAutocomplete">
          <img src="${toolImage}">
          <div>
            <div class="TextAutocomplete">${item.value}</div>
            <div class="typeSoft">${item.type.join("/")}</div>
          </div>
        </div>
      </li>`
      ).appendTo(ul);
    } else if (item.labelnode[0] === "Database") {
      // Create a list item for the autocomplete list.
      return $(`<li>
        <div class="boxAutocomplete">
          <img src="${databaseImage}">
          <div>
            <div class="TextAutocomplete">${item.value}</div>
            <div class="typeSoft">${item.type.join("/")}</div>
          </div>
        </div>
      </li>`
      ).appendTo(ul);
    } else {
      return $(`<li>
        <div class="boxAutocomplete">
          <img src="${topicImage}">
          <div class="TextAutocomplete">${item.value}</div>
        </div>
      </li>`
      ).appendTo(ul);
    }
  };
}



// ------------------------------ Function-8 ------------------------------
/**
 * Removes the legend from the graph.
 */
const removeLegend = () => {
  const legendDiv = $("#legend div")[0];
  // If the legend div is not found, throw an error
  if (!legendDiv) {
    throw new Error("Error in removeLegend: legend div not found");
  }
  // Try to remove all the div elements from the legend
  try {
    legendDiv.innerHTML = "";
  } catch (error) {
    console.log(`Error in removeLegend: ${error.message}`);
    // TODO change the alert link
    appendAlert('While removing the legend, an error has occurred. Please try again and if the problem persists try again in a few minutes.', 'danger');
  }
}



// ------------------------------ Function-9 ------------------------------
/**
 * Adds a legend to the graph, which is a box below the graph that shows
 * the colors of the different clusters and their corresponding labels.
 *
 * If the cluster mode is "Normal", the legend shows the colors of the
 * different types of nodes in the graph, i.e. articles, databases, and
 * tools. If the cluster mode is "Cluster", the legend shows the colors
 * of the different clusters in the graph.
 */
const addLegend = () => {
  showLegend();
  let toolsTopicsDiv = $("#topics-tools-list");
  if ($('#tools-toggle-visibility.hidden, #topics-toggle-visibility.hidden', toolsTopicsDiv).length === $('#tools-toggle-visibility, #topics-toggle-visibility', toolsTopicsDiv).length) {
    $("#legend").addClass("hidden");
  } else {
    $("#legend").removeClass("hidden");
  }
  let optionRadio = $('input[name="cluster_mode"]:checked');
  const list = $("#legend div")[0];
  list.innerHTML = ""; // Clear any previous content in the legend
  if (optionRadio.val() === "Normal") {
    // Add a legend for the different types of nodes in the graph
    list.innerHTML +=
      '<div id="legendnormal"><span id="ExpandedNode" class="bg-lightOrange"></span><span> Expanded node </span></div>';
    list.innerHTML +=
      `<div id="legendnormal"><img class="bg-lightBlue" src=${ToolImage}><span> Tools </span></div>`;
    list.innerHTML +=
      `<div id="legendnormal"><img class="bg-lightPink" src=${PaperImage}><span> Articles </span></div>`;
    list.innerHTML +=
      `<div id="legendnormal"><img class="bg-lightTurquoise" src=${DatabaseImage}><span> Databases </span></div>`;
  } else {
    // Add a legend for the different clusters in the graph
    const dictClusters = returnClusters();
    // Ensure that clusters data is valid
    if (!dictClusters || typeof dictClusters !== 'object') {
      throw new Error("Error in addLegend: clusters data is invalid");
    }
    const listCom = [];
    for (const [, cvalue] of Object.entries(dictClusters)) {
      const clusterValues = Object.values(cvalue);
      // Warn if the cluster data might be incomplete
      if (clusterValues.length < 6) {
        console.warn("Warning in addLegend: cluster data might be incomplete");
        continue;
      }
      listCom.push(clusterValues);
    }
    // Sort clusters by the first value
    const sortedArray = listCom.sort((a, b) => b[0] - a[0]);
    if (sortedArray.length === 0) {
      hideLegend();
    }
    // Add sorted clusters to the legend
    sortedArray.forEach((com) => {
      list.innerHTML +=
        `<div><div id="circle" style="background-color:${com[5]};"></div><span>${com[1]}</span></div>`;
    });
  }
}



// ------------------------------ Function-10 ------------------------------
/**
 * Removes all the nodes from the tools menu.
 */
const removeAllToolsMenu = () => {
  const toolsList = $("#tools-list")[0];
  if (!toolsList) {
    throw new Error("Error in removeAllToolsMenu: tools list not found");
  }
  try {
    toolsList.innerHTML = "";
  } catch (error) {
    console.log(`Error in removeAllToolsMenu: ${error.message}`);
    // TODO change the alert link
    appendAlert('While removing the tools from the menu an error has occurred. Please try again and if the problem persists try again in a few minutes.', 'danger')
  }
}



// ------------------------------ Function-11 ------------------------------
/**
 * Removes all the nodes from the topics menu.
 */
const removeAllTopicsMenu = () => {
  const topicsList = $("#topics-list")[0];
  if (!topicsList) {
    throw new Error("Error in removeAllTopicsMenu: topics list not found");
  }
  try {
    topicsList.innerHTML = "";
  } catch (error) {
    console.log(`Error in removeAllTopicsMenu: ${error.message}`);
    // TODO change the alert link
    appendAlert('While removing the topics from the menu an error has occurred. Please try again and if the problem persists try again in a few minutes.', 'danger')
  }
}



// ------------------------------------------------------------ EXPORTS ------------------------------------------------------------ //

export { actionSidebar, Barchart, sliderRangeFunction, removeLegend, addLegend, initAutocomplete, removeAllToolsMenu, removeAllTopicsMenu };