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
import { returnClusters } from "../main";



// ------------------------------------------------------------ FUNCTIONS ------------------------------------------------------------ //

// ------------------------------ Function-1 ------------------------------
function actionSidebar() {
    if (document.getElementById("MenuImage")) {
      document
        .getElementById("MenuImage")
        .parentElement.removeChild(document.getElementById("MenuImage"));
    }
    var main = document.getElementById("main");
    var button = document.getElementById("openbtn");
    var buttonImage = document.createElement("img");
    buttonImage.id = "MenuImage";
    buttonImage.alt = "";
    if (main.style.marginRight === "0px" || !main.style.marginRight) {
      document.getElementById("mySidebar").style.width = "300px";
      document.getElementById("mySidebar").style.paddingLeft = "10px";
      document.getElementById("main").style.marginRight = "300px";
      //   button.style.background = 'url('+ CloseButton+ ')';
      buttonImage.src = CloseButton;
      document.getElementById("visualization").style.width = "calc(100% - 300px)";
    } else {
      document.getElementById("mySidebar").style.width = "0";
      document.getElementById("mySidebar").style.paddingLeft = "0";
      document.getElementById("main").style.marginRight = "0";
      //   button.innerHTML = '☰';
      buttonImage.src = MenuButton;
      document.getElementById("visualization").style.width = "100%";
    }
    button.appendChild(buttonImage);
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
function drawBar(
    ctx,
    upperLeftCornerX,
    upperLeftCornerY,
    width,
    height,
    color
  ) {
    ctx.save();
    ctx.fillStyle = color;
    ctx.fillRect(upperLeftCornerX, upperLeftCornerY, width, height);
    ctx.restore();
  }



// ------------------------------ Function-4 ------------------------------
var Barchart = function (options) {
  this.options = options;
  this.canvas = options.canvas;
  this.ctx = this.canvas.getContext("2d");
  this.colors = options.colors;

  this.draw = function () {
    var maxValue = 0;
    for (var categ in this.options.data) {
      maxValue = Math.max(maxValue, this.options.data[categ]);
    }
    var canvasActualHeight = this.canvas.height - this.options.padding * 2;
    var canvasActualWidth = this.canvas.width - this.options.padding * 2;

    //drawing the grid lines
    var gridValue = 0;
    while (gridValue <= maxValue) {
      var gridY =
        canvasActualHeight * (1 - gridValue / maxValue) + this.options.padding;
      drawLine(
        this.ctx,
        0,
        gridY,
        this.canvas.width,
        gridY,
        this.options.gridColor
      );

      //writing grid markers
      this.ctx.save();
      this.ctx.fillStyle = this.options.gridColor;
      //             this.ctx.font = "bold 10px Arial";
      //             this.ctx.fillText(gridValue, 10,gridY - 2);
      this.ctx.restore();

      gridValue += this.options.gridScale;
    }

    //drawing the bars
    var barIndex = 0;
    var numberOfBars = Object.keys(this.options.data).length;
    var barSize = canvasActualWidth / numberOfBars;

    for (categ in this.options.data) {
      var val = this.options.data[categ];
      var barHeight = Math.round((canvasActualHeight * val) / maxValue);
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
// Function to scale the horitzontal values of the range slider
function logslider(position) {
    // position will be between 0 and 100
    var minp = 0;
    var maxp = 100;
  
    // The result should be between 100 an 10000000
    var minv = Math.log(parseInt(Object.keys(OccurData)[0]));
    var maxv = Math.log(
      parseInt(Object.keys(OccurData)[Object.keys(OccurData).length - 1])
    );
  
    // calculate adjustment factor
    var scale = (maxv - minv) / (maxp - minp);
  
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
// Exportamos la función de inicialización del autocompletado
function initAutocomplete(toolTopicData, addNodesFn, toolImage, databaseImage, topicImage) {
    $(function () {
      $("#tooltopic_autocomplete").autocomplete({
        source: function (request, response) {
          // Escape regex
          var term = $.ui.autocomplete.escapeRegex(request.term);
          var matcher1 = new RegExp("^" + term, "i"); // Coincidencias que empiezan igual
          var matcher2 = new RegExp("^.+" + term, "i"); // Coincidencias que contienen la búsqueda
  
          // Función para filtrar resultados usando la expresión regular
          function subarray(matcher) {
            return $.grep(toolTopicData, function (item) {
              return matcher.test(item.value);
            });
          }
          // Combinamos los resultados de ambas búsquedas
          response($.merge(subarray(matcher1), subarray(matcher2)));
        },
        minLength: 1, // Número mínimo de caracteres antes de buscar
        select: function (event, ui) {
          var name = ui.item.value;
          var idNode = ui.item.idNodes;
          var labelNode = ui.item.labelnode;
          if (Array.isArray(labelNode)) {
            labelNode = labelNode[0]; // Usa el primer elemento si es un array
          }
          // Llama a la función para agregar nodos
          addNodesFn(name, idNode, labelNode);
          $(this).val(""); // Limpia el campo después de seleccionar
          return false; // Evita el comportamiento predeterminado
        },
        open: function () {
          $(".ui-autocomplete").css("z-index", 1000); // Asegura que la lista de sugerencias esté visible
        },
      }).autocomplete("instance")._renderItem = function (ul, item) {
        // Personalización de los elementos de la lista
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
    });
  }  
  


// ------------------------------ Function-8 ------------------------------
function removeLegend() {
    const list = document.querySelector("#legend div");
    list.innerHTML = "";
  }



// ------------------------------ Function-9 ------------------------------
// Insert the legend in the HTML
function addLegend() {
    var optionRadio = document.querySelector(
      'input[name="cluster_mode"]:checked'
    );
    const list = document.querySelector("#legend div");
    // If normal colors
    if (optionRadio.value === "Normal") {
      // Insert the different type of nodes in the legend (Publication, Tool, Dataset)
  
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
    // If Cluster mode, you take the colors from each community
    // If there are less than 10 nodes, don't write the community in the legend
    else {
      list.innerHTML = "";
      // Retrieve community ids and their size
      var dictClusters = returnClusters();
  
      var listCom = [];
      for (const [, cvalue] of Object.entries(dictClusters)) {
        listCom.push(Object.values(cvalue));
      }
      var sortedArray = listCom.sort(function (a, b) {
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

  

// ------------------------------------------------------------ EXPORTS ------------------------------------------------------------ //

export { actionSidebar, Barchart, sliderRangeFunction, removeLegend, addLegend, initAutocomplete };