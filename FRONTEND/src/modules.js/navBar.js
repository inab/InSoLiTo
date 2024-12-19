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
import MenuButton from "../images/bars-solid.svg";
import ToolImage from "../images/tool_centered_sm.png";
import DatabaseImage from "../images/database_centered_sm.png";
import PaperImage from "../images/paper_centered_sm.png";

// Modules
import { returnClusters, updateNodes } from "./graph";



// ------------------------------------------------------------ FUNCTIONS ------------------------------------------------------------ //

function actionSidebar() {
  try {
    let menuImage = $("#MenuImage");
    if (menuImage.length > 0) {
      menuImage.remove();
    }
    let main = $("#main");
    if (!main || main.length === 0) {
      throw new Error("Main element not found");
    }
    let button = $("#openbtn");
    if (!button || button.length === 0) {
      throw new Error("Open button not found");
    }
    let buttonImage = $('<img id="MenuImage" alt="">');
    if (!buttonImage) {
      throw new Error("Failed to create MenuImage element");
    }
    if (main.css('marginRight') === "0px" || !main.css('marginRight')) {
      $("#mySidebar").css({
        'width': '300px',
        'paddingLeft': '10px'
      });
      main.css('marginRight', "300px");
      buttonImage.attr('src', CloseButton);
      $("#visualization").css('width', "calc(100% - 300px)");
    } else {
      $("#mySidebar").css({
        'width': "0",
        'paddingLeft': "0"
      });
      main.css('marginRight', "0");
      buttonImage.attr('src', MenuButton);
      $("#visualization").css('width', "100%");
    }
    button.append(buttonImage);
  } catch (error) {
    console.error("Error in actionSidebar:", error.message);
    // TODO issue #11
  }
}



// ------------------------------ Function-2 ------------------------------
function drawLine(ctx, startX, startY, endX, endY, color) {
  if (!ctx) {
    throw new Error("drawLine: ctx is null");
  }
  if (typeof startX !== "number" || typeof startY !== "number" || typeof endX !== "number" || typeof endY !== "number") {
    throw new Error("drawLine: start or end coordinates are not numbers");
  }
  ctx.save();
  try {
    ctx.strokeStyle = color;
    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(endX, endY);
    ctx.stroke();
  } finally {
    ctx.restore();
  }
}



// ------------------------------ Function-3 ------------------------------
function drawBar(ctx, upperLeftCornerX, upperLeftCornerY, width, height, color) {
  if (!ctx) {
    throw new Error("drawBar: ctx is null or undefined");
  }
  if (typeof upperLeftCornerX !== "number" || typeof upperLeftCornerY !== "number" ||
      typeof width !== "number" || typeof height !== "number") {
    throw new Error("drawBar: coordinates and dimensions must be numbers");
  }
  ctx.save();
  try {
    ctx.fillStyle = color;
    ctx.fillRect(upperLeftCornerX, upperLeftCornerY, width, height);
  } finally {
    ctx.restore();
  }
}



// ------------------------------ Function-4 ------------------------------
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
  this.draw = function () {
    let maxValue = 0;
    for (let categ in this.options.data) {
      maxValue = Math.max(maxValue, this.options.data[categ]);
    }
    if (maxValue === 0) {
      throw new Error("Barchart: All values in data are zero");
    }
    let canvasActualHeight = this.canvas.height - this.options.padding * 2;
    let canvasActualWidth = this.canvas.width - this.options.padding * 2;
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
function logslider(position) {
  if (typeof position !== "number" || position < 0 || position > 100) {
    throw new Error("logslider: position must be a number between 0 and 100");
  }
  let minp = 0;
  let maxp = 100;
  if (!OccurData || Object.keys(OccurData).length === 0) {
    throw new Error("logslider: OccurData is null or has no keys");
  }
  let minv = Math.log(parseInt(Object.keys(OccurData)[0]));
  let maxv = Math.log(parseInt(Object.keys(OccurData)[Object.keys(OccurData).length - 1]));
  if (isNaN(minv) || isNaN(maxv)) {
    throw new Error("logslider: minv or maxv is not a number");
  }
  let scale = (maxv - minv) / (maxp - minp);
  return Math.trunc(Math.exp(minv + scale * (position - minp)));
}



// ------------------------------ Function-6 ------------------------------
function sliderRangeFunction() {
  if (!YearData || !OccurData) {
    throw new Error("YearData or OccurData is not defined");
  }
  const yearKeys = Object.keys(YearData);
  if (!yearKeys.length) {
    throw new Error("YearData is empty");
  }
  const occurKeys = Object.keys(OccurData);
  if (!occurKeys.length) {
    throw new Error("OccurData is empty");
  }
  $("#year-slider-range").slider({
    range: true,
    min: parseInt(yearKeys[0]),
    max: parseInt(yearKeys[yearKeys.length - 1]),
    values: [
      parseInt(yearKeys[0]),
      parseInt(yearKeys[yearKeys.length - 1]),
    ],
    slide: function (event, ui) {
      $("#yearAmount").val(ui.values[0] + " - " + ui.values[1]);
    },
    change: function () {
      updateNodes();
    },
    create: function () {
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
    values: [20, 100],
    slide: function (event, ui) {
      $("#occurAmount").val(
        logslider(ui.values[0]) + " - " + logslider(ui.values[1])
      );
    },
    change: function () {
      updateNodes();
    },
    create: function () {
      $("#occurAmount").val(
        logslider($("#occur-slider-range").slider("values", 0)) +
        " - " +
        logslider($("#occur-slider-range").slider("values", 1))
      );
    },
  });
}



// ------------------------------ Function-7 ------------------------------
function initAutocomplete(toolTopicData, addNodesFn, toolImage, databaseImage, topicImage) {
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
    source: function (request, response) {
      let term = $.ui.autocomplete.escapeRegex(request.term);
      let matcher1 = new RegExp("^" + term, "i");
      let matcher2 = new RegExp("^.+" + term, "i");
      function subarray(matcher) {
        return $.grep(toolTopicData, function (item) {
          if (!item || typeof item.value !== 'string') {
            return false;
          }
          return matcher.test(item.value);
        });
      }
      response($.merge(subarray(matcher1), subarray(matcher2)));
    },
    minLength: 1,
    select: function (event, ui) {
      let name = ui.item.value;
      let idNode = ui.item.idNodes;
      let labelNode = ui.item.labelnode;
      if (!name || !idNode || !labelNode) {
        throw new Error("Invalid selection: item properties cannot be null or undefined");
      }
      if (Array.isArray(labelNode)) {
        labelNode = labelNode[0];
      }
      addNodesFn(name, idNode, labelNode);
      $(this).val("");
      return false;
    },
    open: function () {
      $(".ui-autocomplete").css("z-index", 1000);
    },
  }).autocomplete("instance")._renderItem = function (ul, item) {
    if (item.labelnode[0] === "Tool") {
      return $('<li><div class="boxAutocomplete"><img src="' +
        toolImage +
        '"><div><div class="TextAutocomplete">' +
        item.value +
        '</div><div class="typeSoft">' +
        item.type.join("/") +
        "</div></div></div></li>"
      ).appendTo(ul);
    } else if (item.labelnode[0] === "Database") {
      return $('<li><div class="boxAutocomplete"><img src="' +
        databaseImage +
        '"><div><div class="TextAutocomplete">' +
        item.value +
        '</div><div class="typeSoft">' +
        item.type.join("/") +
        "</div></div></div></li>"
      ).appendTo(ul);
    } else {
      return $('<li><div class="boxAutocomplete"><img src="' +
        topicImage +
        '"><div class="TextAutocomplete">' +
        item.value +
        "</div></div></li>"
      ).appendTo(ul);
    }
  };
}



// ------------------------------ Function-8 ------------------------------
function removeLegend() {
  const legendDiv = $("#legend div")[0];
  if (!legendDiv) {
    throw new Error("Error in removeLegend: legend div not found");
  }
  try {
    legendDiv.innerHTML = "";
  } catch (error) {
    console.log("Error in removeLegend:", error.message);
    // TODO issue #11
  }
}



function addLegend() {
  let optionRadio = $('input[name="cluster_mode"]:checked');
  const list = $("#legend div")[0];
  list.innerHTML = "";
  if (optionRadio.val() === "Normal") {
    list.innerHTML +=
      '<div id="legendnormal"><span id="ExpandedNode" style="background-color:#fbba7e;"></span><span> Expanded node </span></div>';
    list.innerHTML +=
      `<div id="legendnormal"><img style="background-color: #add8e6;" src=${ToolImage}><span> Tools </span></div>`;
    list.innerHTML +=
      `<div id="legendnormal"><img style="background-color: #FB7E81;" src=${PaperImage}><span> Articles </span></div>`;
    list.innerHTML +=
      `<div id="legendnormal"><img style="background-color: #b2e6ad;" src=${DatabaseImage}><span> Databases </span></div>`;
  } else {
    const dictClusters = returnClusters();
    if (!dictClusters || typeof dictClusters !== 'object') {
      throw new Error("Error in addLegend: clusters data is invalid");
    }
    const listCom = [];
    for (const [, cvalue] of Object.entries(dictClusters)) {
      const clusterValues = Object.values(cvalue);
      if (clusterValues.length < 6) {
        console.warn("Warning in addLegend: cluster data might be incomplete");
        continue;
      }
      listCom.push(clusterValues);
    }
    const sortedArray = listCom.sort((a, b) => b[0] - a[0]);
    sortedArray.forEach((com) => {
      list.innerHTML +=
        `<div><div id="circle" style="background-color:${com[5]};"></div><span>${com[1]}</span></div>`;
    });
  }
}



// ------------------------------ Function-10 ------------------------------
function removeAllToolsMenu() {
  const toolsList = $("#tools-list")[0];
  if (!toolsList) {
    throw new Error("Error in removeAllToolsMenu: tools list not found");
  }
  try {
    toolsList.innerHTML = "";
  } catch (error) {
    console.log("Error in removeAllToolsMenu:", error.message);
    // TODO issue #11
  }
}



// ------------------------------ Function-11 ------------------------------
function removeAllTopicsMenu() {
  const topicsList = $("#topics-list")[0];
  if (!topicsList) {
    throw new Error("Error in removeAllTopicsMenu: topics list not found");
  }
  try {
    topicsList.innerHTML = "";
  } catch (error) {
    console.log("Error in removeAllTopicsMenu:", error.message);
    // TODO issue #11
  }
}



// ------------------------------------------------------------ EXPORTS ------------------------------------------------------------ //

export { actionSidebar, Barchart, sliderRangeFunction, removeLegend, addLegend, initAutocomplete, removeAllToolsMenu, removeAllTopicsMenu };