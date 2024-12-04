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

// Modules
import { returnClusters, updateNodes } from "./graph";



// ------------------------------------------------------------ FUNCTIONS ------------------------------------------------------------ //

// ------------------------------ Function-1 ------------------------------
function actionSidebar() {
  if ($("#MenuImage").length > 0) {
    $("#MenuImage").remove()
  }
  let main = $("#main");
  let button = $("#openbtn");
  let buttonImage = $('<img id="MenuImage" alt="">');
  if (main.css('marginRight') === "0px" || !main.css('marginRight')) {
    $("#mySidebar").css({
      'width': '300px',
      'paddingLeft': '10px'
    });
    main.css('marginRight', "300px");
    buttonImage.attr('src', CloseButton)
    $("#visualization").css('width', "calc(100% - 300px)");
  } else {
    $("#mySidebar").css({
      'width': "0",
      'paddingLeft': "0"
    });
    main.css('marginRight', "0");
    buttonImage.attr('src', MenuButton)
    $("#visualization").css('width', "100%");
  }
  button.append(buttonImage);
}



// ------------------------------ Function-2 ------------------------------
function drawLine(ctx, startX, startY, endX, endY, color) {
  ctx.save();
  ctx.strokeStyle = color;
  ctx.beginPath();
  ctx.moveTo(startX, startY);
  ctx.lineTo(endX, endY);
  ctx.stroke();
  ctx.restore();
}



// ------------------------------ Function-3 ------------------------------
function drawBar(ctx, upperLeftCornerX, upperLeftCornerY, width, height, color) {
  ctx.save();
  ctx.fillStyle = color;
  ctx.fillRect(upperLeftCornerX, upperLeftCornerY, width, height);
  ctx.restore();
}



// ------------------------------ Function-4 ------------------------------
let Barchart = function (options) {
  this.options = options;
  this.canvas = options.canvas;
  this.ctx = this.canvas.getContext("2d");
  this.colors = options.colors;
  this.draw = function () {
    let maxValue = 0;
    for (let categ in this.options.data) {
      maxValue = Math.max(maxValue, this.options.data[categ]);
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
    let barSize = canvasActualWidth / numberOfBars;
    for (let categ in this.options.data) {
      let val = this.options.data[categ];
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
  let minp = 0;
  let maxp = 100;
  let minv = Math.log(parseInt(Object.keys(OccurData)[0]));
  let maxv = Math.log(
    parseInt(Object.keys(OccurData)[Object.keys(OccurData).length - 1])
  );
  let scale = (maxv - minv) / (maxp - minp);
  return Math.trunc(Math.exp(minv + scale * (position - minp)));
}



// ------------------------------ Function-6 ------------------------------
function sliderRangeFunction() {
  $("#year-slider-range").slider({
    range: true,
    min: parseInt(Object.keys(YearData)[0]),
    max: parseInt(Object.keys(YearData)[Object.keys(YearData).length - 1]),
    values: [
      parseInt(Object.keys(YearData)[0]),
      parseInt(Object.keys(YearData)[Object.keys(YearData).length - 1]),
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
};



// ------------------------------ Function-7 ------------------------------
function initAutocomplete(toolTopicData, addNodesFn, toolImage, databaseImage, topicImage) {
  $("#tooltopic_autocomplete").autocomplete({
    source: function (request, response) {
      let term = $.ui.autocomplete.escapeRegex(request.term);
      let matcher1 = new RegExp("^" + term, "i");
      let matcher2 = new RegExp("^.+" + term, "i");
      function subarray(matcher) {
        return $.grep(toolTopicData, function (item) {
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
  const list = document.querySelector("#legend div");
  list.innerHTML = "";
}



// ------------------------------ Function-9 ------------------------------
function addLegend() {
  let optionRadio = $('input[name="cluster_mode"]:checked');
  const list = $("#legend div")[0];
  if (optionRadio.value === "Normal") {
    list.innerHTML =
      '<div id="legendnormal"><span id="ExpandedNode" style="background-color:#fbba7e;"></span><span> Expanded node </span></div>';
    list.innerHTML +=
      '<div id="legendnormal"><img style="background-color: #add8e6;" src=' +
      ToolImage +
      " ><span> Tools </span></div>";
    list.innerHTML +=
      '<div id="legendnormal"><img style="background-color: #FB7E81;" src=' +
      PaperImage +
      "><span> Articles </span></div>";
    list.innerHTML +=
      '<div id="legendnormal"><img style="background-color: #b2e6ad;" src=' +
      DatabaseImage +
      "><span> Databases </span></div>";
  }
  else {
    list.innerHTML = "";
    let dictClusters = returnClusters();
    let listCom = [];
    for (const [, cvalue] of Object.entries(dictClusters)) {
      listCom.push(Object.values(cvalue));
    }
    let sortedArray = listCom.sort(function (a, b) {
      return b[0] - a[0];
    });
    sortedArray.forEach((com) => {
      list.innerHTML +=
        '<div><div id="circle" style="background-color:' +
        com[5] +
        ';"></div><span>' +
        com[1] +
        "</span></div>";
    });
  }
}



// ------------------------------ Function-10 ------------------------------
function removeAllToolsMenu() {
  $("#tools-list").html("");
}



// ------------------------------ Function-11 ------------------------------
function removeAllTopicsMenu() {
  $("#topics-list").html("");
}



// ------------------------------------------------------------ EXPORTS ------------------------------------------------------------ //

export { actionSidebar, Barchart, sliderRangeFunction, removeLegend, addLegend, initAutocomplete, removeAllToolsMenu, removeAllTopicsMenu };