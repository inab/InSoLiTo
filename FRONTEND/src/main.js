// Dependencies
import $ from "jquery";
import "jquery-ui/ui/core";
import "jquery-ui/ui/widgets/slider.js";
import "jquery-ui/ui/widgets/autocomplete.js";
import vis from "vis-network/dist/vis-network.min.js";

// Style
import "jquery-ui/themes/base/theme.css";
import "jquery-ui/themes/base/slider.css";
import "vis-network/dist/dist/vis-network.min.css";
import "./styles/style.css";

//JSON
import sampleConfig from "./config.json";
import OccurData from "../../DB/RelationshipSliderData.json";
import YearData from "../../DB/YearSliderData.json";
import ToolTopicData from "../../DB/ToolTopicAutocomplete.json";
import communityData from "../../DB/CommunityData.json";

//Images
import ToolImage from "./images/tool_centered_sm.png";
import PaperImage from "./images/paper_centered_sm.png";
import DatabaseImage from "./images/database_centered_sm.png";
import TopicImage from "./images/topic_centered_sm.png";
import CloseButton from "./images/xmark-solid.svg";
import MenuButton from "./images/bars-solid.svg";
import LoadingIcon from "./images/spinner-solid.svg";
import logoInSoLiTo from "./images/logo_InSoLiTo.png";

// Neovis.js options
var Vis;
var nodes;
var edges;

/**
 * Esta función se encarga de primero instanciar los nodos(nodes) y las 
 * aristas(edges), luego configura la red y por ultimo la crea.
 */
function drawVis() {
  //Crea los nodos y las aristas
  nodes = new vis.DataSet();
  edges = new vis.DataSet();
  //Comienza la configuración de la red
  var container = document.getElementById("VisNetwork");
  var data = {
    nodes: nodes,
    edges: edges,
  };
  var options = {
    layout: {
      randomSeed: 34,
    },
    physics: {
      forceAtlas2Based: {
        gravitationalConstant: -200,
        //                             centralGravity: 0.005,
        springLength: 400,
        springConstant: 0.36,
        avoidOverlap: 1,
      },
      maxVelocity: 30,
      solver: "forceAtlas2Based",
      timestep: 1,
      adaptiveTimestep: true,
      stabilization: {
        enabled: true,
        iterations: 2000,
        updateInterval: 25,
        fit: true,
      },
    },
    interaction: {
      tooltipDelay: 200,
      navigationButtons: true,
    },
    nodes: {
      font: {
        size: 26,
        strokeWidth: 7,
      },
      scaling: {},
      shapeProperties: {
        interpolation: false, // 'true' for intensive zooming
      },
    },
    edges: {
      length: 200,
    },
  };
  //Crea la red para que se pueda visualizar.
  Vis = new vis.Network(container, data, options);
}

/**
 * Esta función se encarga de gestionar la sidebar. Si esta abierta
 * pone el icono de cerrarlo y hacer que el icono sea el boton de cerrarlo
 * y si esta cerrada pone el icono de abrir la sidebar y carga sus elementos.
 */
function actionSidebar() {
  //Eliminar el icono de la sidebar si ya existe.
  if (document.getElementById("MenuImage")) {
    document
      .getElementById("MenuImage")
      .parentElement.removeChild(document.getElementById("MenuImage"));
  }
  //Definir variables importantes
  var main = document.getElementById("main");
  var button = document.getElementById("openbtn");
  var buttonImage = document.createElement("img");
  buttonImage.id = "MenuImage";
  buttonImage.alt = "";
  //Condicional para abrir o cerrar la sidebar dependiendo de si esta abierta o cerrada
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
  //Añadir el icono al botón
  button.appendChild(buttonImage);
}

//Aqui añade la funcion de la sidebar de arriba al event listener del botón.
var navButton = document.getElementById("openbtn");
navButton.addEventListener("click", () => {
  actionSidebar();
});

/**
 * Esta función elimina el elemento del DOM que se encarga de mostrar
 * la pagina de cargando.
 */
function removeLoadingPage() {
  var loadingPage = document.getElementById("enter-webpage");
  loadingPage.parentElement.removeChild(loadingPage);
}

/**
 * Esta función crea la imagen de la home dinamicamente y la añade a 
 * a la pagina de la home
 */
function createHomePage() {
  //Coge el contendor principal
  var homePage = document.getElementById("inital-screen");
  //Crea el div que contendrá la imagen y el elemento imagen
  var divHomePage = document.createElement("div");
  var imgHomePage = document.createElement("img");
  //Añadirle la imagen al elemento imagen
  imgHomePage.src = logoInSoLiTo;
  imgHomePage.className = "imgHomePageeee";
  imgHomePage.alt = "InSoLiTo Logo";
  //Añadirlo al documento
  divHomePage.appendChild(imgHomePage);
  homePage.insertBefore(divHomePage, homePage.firstChild);
}

/**
 * Invocar los metodos creados anteriormente cuando la ventana se cargue
 */
window.onload = createHomePage();

window.onload = removeLoadingPage();

window.onload = drawVis();

window.onload = actionSidebar();

// Barchart functions
/**
 * Esta función dibuja la linea desde un punto inicial hasta un punto final con
 * un color determinado.
 */
function drawLine(ctx, startX, startY, endX, endY, color) {
  ctx.save();
  ctx.strokeStyle = color;
  ctx.beginPath();
  ctx.moveTo(startX, startY);
  ctx.lineTo(endX, endY);
  ctx.stroke();
  ctx.restore();
}

/**
 * Esta función dibuja un rectangulo/barra en el html especificando las 
 * coordenadas de la esquina superior izquierda, el ancho, el ato y el 
 * color de la barra.
 */
function drawBar(ctx, upperLeftCornerX, upperLeftCornerY, width, height, color) {
  ctx.save();
  ctx.fillStyle = color;
  ctx.fillRect(upperLeftCornerX, upperLeftCornerY, width, height);
  ctx.restore();
}

/**
 * Esta función permite dibujar un grafico de barras en html utilizando tanto
 * los metodos de arriba como datos y configuraciones personalizadas.
 */
var Barchart = function (options) {
  this.options = options;
  this.canvas = options.canvas;
  this.ctx = this.canvas.getContext("2d");
  this.colors = options.colors;

  //El metodo draw hace todos los pasos necesarios para dibujar el grafico.
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

//Selecciona el "lienzo" sobre el que se pintará el gráfico
var YearCanvas = document.getElementById("YearCanvas");
// Configura las opciones del gráfico
var YearBarchart = new Barchart({
  canvas: YearCanvas,
  padding: 0,
  data: YearData,
  colors: ["#0b579f"],
});
// Dibuja el gráfico de barras
YearBarchart.draw();

//Selecciona el lienzo
var OccurCanvas = document.getElementById("OccurCanvas");
// Configura el grafico de barras
var OccurBarchart = new Barchart({
  canvas: OccurCanvas,
  padding: 0,
  data: OccurData,
  colors: ["#0b579f"],
});
// Lo dibuja
OccurBarchart.draw();

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

// Slider range function
$(function () {
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
    // When slider range changes, update the nodes
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

  // Slider range function
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
    // When slider range changes, update the nodes
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
});

// Function to update InSoLiTo everytime the range slider changes
function updateNodes() {
  // Take name and id of all the tools and topics in the Label Menu
  // Store the values in the dictionary
  var nameNodeDict = {};
  ["ToolButton", "topicDiv"].forEach((className) => {
    var listLegend = document.getElementsByClassName(className);
    for (var i = 0; i < listLegend.length; i++) {
      var nameNode = listLegend[i].textContent;
      var nodeInformation = listLegend[i].value;
      if (className === "ToolButton") {
        var typeNode = "Tool";
      } else {
        var typeNode = "Topic";
      }
      nameNodeDict[nameNode] = [nodeInformation, typeNode];
    }
  });
  // Clear the webpage
  reset();
  // Readd the nodes from the Label Menu
  for (const [nameNode, listNode] of Object.entries(nameNodeDict)) {
    // Take the Min and Max cooccurrence value between the relationships
    addNodes(nameNode, listNode[0], listNode[1]);
  }
}

// Autcomplete Function for the Search box
$(function () {
  $("#tooltopic_autocomplete")
    .autocomplete({
      source: function (request, response) {
        // Escape regex
        var term = $.ui.autocomplete.escapeRegex(request.term);
        // Search results that start with the search term
        var matcher1 = new RegExp("^" + term, "i");
        // Search results that start differently
        var matcher2 = new RegExp("^.+" + term, "i");

        function subarray(matcher) {
          return $.grep(ToolTopicData, function (item) {
            return matcher.test(item.value);
          });
        }
        response($.merge(subarray(matcher1), subarray(matcher2)));
      },
      minLength: 1,
      select: function (event, ui) {
        // Select Name and Id of tool
        var name = ui.item.value;
        var idNode = ui.item.idNodes;
        var labelNode = ui.item.labelnode;
        if (Array.isArray(labelNode)) {
          var labelNode = labelNode[0];
        }
        //Add Nodes from the autocomplete
        addNodes(name, idNode, labelNode);
        $(this).val("");
        return false;
      },
      open: function () {
        $(".ui-autocomplete").css("z-index", 1000);
      },
    }) // Output of the textbox
    .autocomplete("instance")._renderItem = function (ul, item) {
    if (item.labelnode[0] === "Tool") {
      return $(
        '<li><div class="boxAutocomplete"><img src="' +
          ToolImage +
          '"><div><div class="TextAutocomplete">' +
          item.value +
          '</div><div class="typeSoft">' +
          item.type.join("/") +
          "</div></div></div></li>"
      ).appendTo(ul);
    } else if (item.labelnode[0] === "Database") {
      return $(
        '<li><div class="boxAutocomplete"><img src="' +
          DatabaseImage +
          '"><div><div class="TextAutocomplete">' +
          item.value +
          '</div><div class="typeSoft">' +
          item.type.join("/") +
          "</div></div></div></li>"
      ).appendTo(ul);
    } else {
      return $(
        '<li><div class="boxAutocomplete"><img src="' +
          TopicImage +
          '"><div class="TextAutocomplete">' +
          item.value +
          "</div></div></li>"
      ).appendTo(ul);
    }
  };
});

// Empty the legend
function removeLegend() {
  const list = document.querySelector("#legend div");
  list.innerHTML = "";
}

// Function that retrieves the id and size of the communities from the graph
function returnClusters() {
  var net = Vis.body;
  var allNodes = net.nodeIndices;

  var dictClusters = {};

  // For each node found in the graph
  allNodes.forEach((node) => {
    // Store their id and color
    var commId = net.nodes[node].options.group;
    var colorId = net.nodes[node].options.color.background;

    // Count how many times the same community is found
    if (dictClusters.hasOwnProperty(commId)) {
      dictClusters[commId].count += 1;
    }
    // If the node has an unknow community, initialize it
    else {
      dictClusters[commId] = {
        count: 1,
        mTopic: "Undefined",
        mLanguage: "Undefinded",
        mOS: "Undefined",
        tNodesDB: 0,
        color: colorId,
      };
    }
  });
  communityData.forEach((community) => {
    if (dictClusters[community.id]) {
      if (community.Topic) {
        dictClusters[community.id].mTopic = community.Topic;
      }
      if (community.Language) {
        dictClusters[community.id].mLanguage = community.Language;
      }
      if (community.OS) {
        dictClusters[community.id].mOS = community.OS;
      }
      dictClusters[community.id].tNodesDB = community.totalNodes;
    }
  });
  return dictClusters;
}

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

// Function that store the community color of the nodes
// And store the color representing the type of node that they are (Publication, Tool, Database)
function storeClusterColor() {
  setTimeout(function () {
    var net = Vis.body;
    var allNodes = net.nodeIndices;

    var listLegend = document.getElementsByClassName("ToolButton");
    var centeredNodes = [];
    for (var i = 0; i < listLegend.length; i++) {
      centeredNodes.push(listLegend[i].value);
    }
    // For each node
    allNodes.forEach((node) => {
      // if (net.nodes[node].options.hasOwnProperty('colorcluster')){
      // 	return true;
      // }
      // Create a dictionary for storing the color of the Cluster mode
      var objCluster = {
        colorcluster: {
          background: null,
          border: null,
          highlight: { background: null, border: null },
          hover: { background: null, border: null },
        },
      };
      // Store the color of the community
      objCluster.colorcluster.background =
        net.nodes[node].options.color.background;
      objCluster.colorcluster.border = net.nodes[node].options.color.border;
      objCluster.colorcluster.highlight.background =
        net.nodes[node].options.color.highlight.background;
      objCluster.colorcluster.highlight.border =
        net.nodes[node].options.color.highlight.border;
      objCluster.colorcluster.hover.background =
        net.nodes[node].options.color.hover.background;
      objCluster.colorcluster.hover.border =
        net.nodes[node].options.color.hover.border;
      // Insert the colors of the different type of nodes in the dictionary
      var objNormal = {
        colornormal: {
          background: null,
          border: null,
          highlight: { background: null, border: null },
          hover: { background: null, border: null },
        },
      };

      if (net.nodes[node].options.Neo4jLabel === "Tool") {
        objNormal.colornormal.background = "#add8e6";
        objNormal.colornormal.border = "#6bc5e3";
        objNormal.colornormal.highlight.background = "#add8e6";
        objNormal.colornormal.highlight.border = "#6bc5e3";
        objNormal.colornormal.hover.background = "#add8e6";
        objNormal.colornormal.hover.border = "#6bc5e3";
      } else if (net.nodes[node].options.Neo4jLabel === "Database") {
        objNormal.colornormal.background = "#b2e6ad";
        objNormal.colornormal.border = "#4ed442";
        objNormal.colornormal.highlight.background = "#b2e6ad";
        objNormal.colornormal.highlight.border = "#4ed442";
        objNormal.colornormal.hover.background = "#b2e6ad";
        objNormal.colornormal.hover.border = "#4ed442";
      } else {
        objNormal.colornormal.background = "#FB7E81";
        objNormal.colornormal.border = "#FA0A10";
        objNormal.colornormal.highlight.background = "#FB7E81";
        objNormal.colornormal.highlight.border = "#FA0A10";
        objNormal.colornormal.hover.background = "#FB7E81";
        objNormal.colornormal.hover.border = "#FA0A10";
      }
      // Insert the colors of the different type of nodes in the dictionary
      if (centeredNodes.includes(node)) {
        objNormal.colornormal.background = "#fbba7e";
        objNormal.colornormal.border = "#f99234";
        objNormal.colornormal.highlight.background = "#fbba7e";
        objNormal.colornormal.highlight.border = "#f99234";
        objNormal.colornormal.hover.background = "#fbba7e";
        objNormal.colornormal.hover.border = "#f99234";
      }

      // Update the nodes with the color information
      net.nodes[node].options = Object.assign(
        net.nodes[node].options,
        objCluster
      );
      net.nodes[node].options = Object.assign(
        net.nodes[node].options,
        objNormal
      );
    });
  });
}

// Function that changes the color of the nodes - Cluster/Normal mode
function clusterMode() {
  // Check the color mode
  var optionRadio = document.querySelector(
    'input[name="cluster_mode"]:checked'
  );
  // List where the new colors of the nodes will be stored
  var listChanges = [];
  // Variables to shorten paths
  var net = Vis.body;
  var allNodes = net.nodeIndices;
  // For each node displayed
  allNodes.forEach((node) => {
    // Path for Cluster Mode
    if (optionRadio.value === "Cluster") {
      var colorNodePath = net.nodes[node].options.colorcluster;
    }
    // Path for Normal Mode
    else {
      var colorNodePath = net.nodes[node].options.colornormal;
    }
    // Assign new color to node
    var changeNode = {
      id: node,
      color: {
        background: colorNodePath.background,
        border: colorNodePath.border,
        highlight: {
          border: colorNodePath.highlight.border,
          background: colorNodePath.highlight.background,
        },
        hover: {
          border: colorNodePath.hover.border,
          background: colorNodePath.hover.background,
        },
      },
    };
    listChanges.push(changeNode);
  });

  // Update nodes
  nodes.update(listChanges);
}

$("input[type=radio][name=cluster_mode]").change(function () {
  // Change color of the nodes
  clusterMode();
  // Update legend
  addLegend();
});

$("input[type=checkbox][name=displayArticles]").change(function () {
  // Update Nodes
  updateNodes();
});

$("input[type=radio][name=typeOfEdges]").change(function () {
  // Update Nodes
  updateNodes();
  var optionEdges = document.querySelector("input[name=typeOfEdges]:checked");
  if (optionEdges.value === "allYearsEdges") {
    document.getElementById("yearColumn").style.display = "none";
  } else {
    document.getElementById("yearColumn").style.display = "block";
  }
});

// Initialize Menu
function algo() {
  // When node selected, activate the menu
  Vis.on("selectNode", (e1) => {
    menu(e1);
  });
  // When nodes are not selected, delete the menu
  Vis.on("deselectNode", () => {
    var contextMenu = document.getElementById("context-menu");
    contextMenu.innerHTML = "";
  });
}

// Remove all the Tools and Topics from the Label Menu
function removeAllToolsMenu() {
  const list = document.getElementById("tools-list");
  list.innerHTML = "";
}
// Remove all the Tools and Topics from the Label Menu
function removeAllTopicsMenu() {
  const list = document.getElementById("topics-list");
  list.innerHTML = "";
}
//Esta función agrega los nodos y aristas a una visualización ya configurada.
function createVisVisualization(nodeDataArray, edgeDataArray) {
  nodes.add(nodeDataArray);
  edges.add(edgeDataArray);
}

/**
 * En resumen, esta función postData envía datos JSON a una URL específica
 * mediante una solicitud POST, utilizando fetch. Añade encabezados para 
 * definir el formato y autenticación, y devuelve la respuesta como un objeto JSON.
 */
async function postData(url = "", data = {}) {
  const response = await fetch(url, {
    method: "POST", // *GET, POST, PUT, DELETE, etc.
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json;charset=UTF-8",
      "Access-Mode": "READ",
      Authorization: (
        sampleConfig.serverUser +
        ":" +
        sampleConfig.serverPassword
      ).toString("base64"),
    },
    body: JSON.stringify(data), // body data type must match "Content-Type" header
  });
  return response.json(); // parses JSON response into native JavaScript objects
}

/**
 * Esta función hace una consulta con lenguage cypher (lenguaje para las bases de 
 * datos tipo Neo4j) en un servidor configurado y luego actualiza una visualización 
 * de red con los datos obtenidos.
 * 
 * @param cypherQuery Es la consulta Cypher que ejecutará la función
 */
function updateWithCypher(cypherQuery) {
  //Crear el objeto input data con estructura adecuada para Neo4j
  var inputData = {
    statements: [
      {
        statement: cypherQuery, //Consulta a ejecutar
        resultDataContents: ["graph"], //Especificar el tipo de datos que se desea recibir
      },
    ],
  };

  //Llama al metodo que hemos configurado antes y cuando se complete
  //se ejecuta el bloque de codigo que contiene el .then((x)=>{})
  postData(sampleConfig.serverUrl, inputData).then((datainput) => {
    var edgeDataArray = [];
    var nodeDataArray = [];
    const idNodesSet = new Set(); 
    Vis.body.nodeIndices.forEach(idNodesSet.add, idNodesSet);
    const idEdgesSet = new Set();
    Vis.body.edgeIndices.forEach(idEdgesSet.add, idEdgesSet);
    datainput.results[0].data.forEach((element) => {
      element.graph.nodes.forEach((nodeElement) => {
        if (!idNodesSet.has(nodeElement.id)) {
          idNodesSet.add(nodeElement.id);
          if (nodeElement.labels[0] === "Publication") {
            nodeDataArray.push({
              id: nodeElement.id,
              label: nodeElement.properties.subtitle,
              group: nodeElement.properties.community,
              Neo4jLabel: nodeElement.labels[0],
              properties: nodeElement.properties,
              shape: "circularImage",
              image: PaperImage,
              title: nodeElement.properties.title,
            });
          } else {
            var imageLabel;
            if (nodeElement.labels[0] === "Tool") {
              imageLabel = ToolImage;
            } else if (nodeElement.labels[0] === "Database") {
              imageLabel = DatabaseImage;
            }
            nodeDataArray.push({
              id: nodeElement.id,
              label: nodeElement.properties.name,
              group: nodeElement.properties.community,
              Neo4jLabel: nodeElement.labels[0],
              properties: nodeElement.properties,
              shape: "circularImage",
              image: imageLabel,
            });
          }
        }
      });
      element.graph.relationships.forEach((edgeElement) => {
        if (!idEdgesSet.has(edgeElement.id)) {
          idEdgesSet.add(edgeElement.id);
          if (edgeElement.type === "METAOCCUR_ALL") {
            edgeDataArray.push({
              id: edgeElement.id,
              from: edgeElement.startNode,
              to: edgeElement.endNode,
              value: edgeElement.properties.times,
              color: { inherit: "both" },
            });
          } else {
            edgeDataArray.push({
              id: edgeElement.id,
              from: edgeElement.startNode,
              to: edgeElement.endNode,
              value: edgeElement.properties.times,
              color: { inherit: "both" },
              title: edgeElement.properties.year,
            });
          }
        }
      });
    });
    //Se llama al metodo que hace que todo se visualice en la web.
    createVisVisualization(nodeDataArray, edgeDataArray);
  });
}

// Run a Cypher query that will be displayed in the web
/**
 * La función addNodesGraph genera una consulta Cypher para Neo4j en función de los 
 * parámetros dados, ejecuta la consulta, y muestra un gráfico de nodos y relaciones 
 * filtrados por las condiciones establecidas. Esta función también controla la 
 * interfaz de usuario para dar retroalimentación visual mientras la consulta se ejecuta.
 */
async function addNodesGraph(nameNode, idNode, nodeType) {
  //Checkbox que indica si deben mostrarse los articulos seleccionados
  var displayArticles = document.getElementById("displayArticles").checked;
  var displayArticles = document.getElementById("displayArticles").checked;
  //Tipo de relación entre los nodos
  var typeOfEdges = document.querySelector('input[name="typeOfEdges"]:checked');
  // Take the Min and Max cooccurrence value between the relationships
  var cMin = $("#occurAmount")
    .val()
    .substr(0, $("#occurAmount").val().indexOf("-") - 1);
  var cMax = $("#occurAmount")
    .val()
    .substr(
      $("#occurAmount").val().indexOf("-") + 2,
      $("#occurAmount").val().length
    );
  var yMin = $("#yearAmount")
    .val()
    .substr(0, $("#yearAmount").val().indexOf("-") - 1);
  var yMax = $("#yearAmount")
    .val()
    .substr(
      $("#yearAmount").val().indexOf("-") + 2,
      $("#yearAmount").val().length
    );

  // Cypher query
  var cypherQuery = "";
  if (nodeType === "Topic") {
    if (typeOfEdges.value === "allYearsEdges") {
      cypherQuery =
        'match (n)-[:TOPIC]->(k:Keyword)-[:SUBCLASS*]->(k2:Keyword) where k2.label="' +
        nameNode +
        '" or k.label="' +
        nameNode +
        '" with distinct n with collect(n) as nt unwind nt as nt1 unwind nt as nt2 match (nt1)-[m:METAOCCUR_ALL]-(nt2) where m.times>=' +
        cMin +
        " and m.times<= " +
        cMax +
        " return nt1,m,nt2";
    } else {
      cypherQuery =
        'match (n)-[:TOPIC]->(k:Keyword)-[:SUBCLASS*]->(k2:Keyword) where k2.label="' +
        nameNode +
        '" or k.label="' +
        nameNode +
        '" with distinct n with collect(n) as nt unwind nt as nt1 unwind nt as nt2 match (nt1)-[m:METAOCCUR]-(nt2) where m.times>=' +
        cMin +
        " and m.times<= " +
        cMax +
        " and m.year>=" +
        yMin +
        " and m.year<=" +
        yMax +
        " return nt1,m,nt2";
    }
  } else {
    if (displayArticles) {
      if (typeOfEdges.value === "allYearsEdges") {
        cypherQuery =
          'MATCH (i)-[o:METAOCCUR_ALL]-(p) where i.name="' +
          nameNode +
          '" and o.times>=' +
          cMin +
          " and o.times<=" +
          cMax +
          " return i,o,p order by o.times";
      } else {
        cypherQuery =
          'MATCH (i)-[o:METAOCCUR]-(p) where i.name="' +
          nameNode +
          '" and o.times>=' +
          cMin +
          " and o.times<=" +
          cMax +
          " and o.year>=" +
          yMin +
          " and o.year<=" +
          yMax +
          "  return i,o,p order by o.times";
      }
    } else {
      if (typeOfEdges.value === "allYearsEdges") {
        cypherQuery =
          'MATCH (i)-[o:METAOCCUR_ALL]-(p) where i.name="' +
          nameNode +
          '" and o.times>=' +
          cMin +
          " and o.times<=" +
          cMax +
          " and not p:Publication return i,o,p order by o.times";
      } else {
        cypherQuery =
          'MATCH (i)-[o:METAOCCUR]-(p) where i.name="' +
          nameNode +
          '" and o.times>=' +
          cMin +
          " and o.times<=" +
          cMax +
          " and not p:Publication and o.year>=" +
          yMin +
          " and o.year<=" +
          yMax +
          " return i,o,p order by o.times";
      }
    }
  }
  // Run query
  var nodesBeforeQuery = nodes.length;
  // Update nodes
  updateWithCypher(cypherQuery);
  // console.log(cypherQuery);
  document.getElementById("inital-screen").style.display = "none";

  // Display loading screen until the query is fully displayed

  const LoadingImg = document.getElementById("loadingSpinner");
  LoadingImg.src = LoadingIcon;
  LoadingImg.style.display = "block";

  const list = document.getElementById("loading");
  list.style.display = "block";

  // If no results found, wait and put an alert
  await new Promise((r) => setTimeout(r, 15000));
  if (nodes.length === 0 || nodes.length === nodesBeforeQuery) {
    alert("No results found. Try again!");
    list.style.display = "none";
    // return;
  }
  if (nodeType === "Topic") {
    addTopicLabelMenu(nameNode);
  } else {
    addToolLabelMenu(nameNode, idNode);
  }

  // Initialize Right-click Menu
  algo();
  // Wait until the colors of the nodes are stored and fully displayed in the web
  await new Promise(() => {
    storeClusterColor();
    waitAddTool();
  });
}

// Function to add nodes in the web and insert their names in the Label Menu
/**
 * La función addNodes verifica si un nodo con un nombre específico ya existe 
 * en un menú de etiquetas en la interfaz. Si el nombre no está presente, llama 
 * a otra función (addNodesGraph) para agregar el nodo al gráfico o visualización 
 * correspondiente.
 */
function addNodes(nameNode, idNode, nodeType) {
  // Remove menu
  var contextMenu = document.getElementById("context-menu");
  contextMenu.innerHTML = "";
  //Search the name in the labels menu
  var list = document.getElementsByClassName("delete");
  var isInMenu = false;
  // If name already in the label menu
  Array.prototype.forEach.call(list, function (tool) {
    if (tool.textContent === nameNode) {
      isInMenu = true;
    }
  });
  // If name of tool/topic not in menu
  if (isInMenu === false) {
    addNodesGraph(nameNode, idNode, nodeType);
  }
}

// Function to only display the node centered
function centerNode(name, idNode) {
  // Reset the webpage
  reset();
  removeAllTopicsMenu();
  // Add the tool
  addNodes(name, idNode, "Tool");
}

/**
 * La función addTopicLabelMenu agrega un nuevo tema al menú de etiquetas 
 * si aún no está presente. Esto evita duplicados y asegura que solo se 
 * añadan temas únicos.
 */
function addTopicLabelMenu(NameTopic) {
  var topicDivElements = document.getElementsByClassName("topicDiv");
  for (var i = 0; i < topicDivElements.length; i++) {
    if (topicDivElements[i].innerText === NameTopic) {
      return;
    }
  }
  var divTopic = document.createElement("div");
  divTopic.className = "topicDiv";
  divTopic.innerText = NameTopic;
  document.getElementById("topics-list").appendChild(divTopic);
}

// Add tools and topics displayed in the webpage in the Label Menu
// Also, when they are click, remove their nodes from the graph
function addToolLabelMenu(NameTopic, idNode) {
  var buttonTool = document.createElement("button");
  buttonTool.className = "ToolButton";
  // buttonTool.innerText = NameTopic;
  buttonTool.value = idNode;

  buttonTool.innerHTML =
    '<img class="close-icon" src="' +
    CloseButton +
    '"/>' +
    '<div class="name-topic">' +
    NameTopic +
    "</div>";

  document.getElementById("tools-list").appendChild(buttonTool);

  var buttonTool = document.getElementsByClassName("ToolButton");
  for (var i = 0; i < buttonTool.length; i++) {
    buttonTool[i].addEventListener("click", function (e) {
      // Store node ID
      var IdTool = e.currentTarget.value;
      e.currentTarget.parentNode.removeChild(e.currentTarget);
      // Take all the nodes connected to the tool clicked
      var ConnectedNodes = Vis.getConnectedNodes(IdTool);

      // Take the nodes only having 1 connection
      var UnconnectedNodes = [];
      ConnectedNodes.forEach((node) => {
        if (Vis.getConnectedEdges(node).length === 1) {
          UnconnectedNodes.push(node);
        }
      });
      // Remove the tool selected and the nodes connected to it having 1 connection
      Vis.selectNodes([IdTool].concat(UnconnectedNodes));
      Vis.deleteSelected();

      // If there is any node with no connections, remove it
      var graphNodes = Vis.body.nodeIndices;
      graphNodes.forEach((node) => {
        if (Vis.getConnectedNodes(node).length === 0) {
          Vis.selectNodes([node]);
          Vis.deleteSelected();
        }
      });
      // Update the legend
      addLegend();
    });
  }
}

//Right-Click menu
// From the tool selected, with a right-click event you display a menu to do the following:
// Know which EDAM terms it belongs. If the term is clicked, it will be displayed in the graph
// Webpage in OpenEBench
// Center the node
// Expand the node
function menu(e1) {
  // if node exist
  if (e1.nodes.length === 1) {
    // Take node ID
    var nodeId = e1.nodes[0];
    // If the node is a publcation, do nothing
    if (Vis.body.nodes[nodeId].options.Neo4jLabel === "Publication") {
      return;
    }

    // Initialize menu

    var name = Vis.body.nodes[nodeId].options.properties.name;

    const contextMenu = document.getElementById("context-menu");
    contextMenu.innerHTML =
      '<div class="item" id="nameTool">' +
      name +
      '</div><div class="topicmenu" id="topic"></div><div class="item" id = "webpage"></div><div class="item" id="center"></div><div class="item" id="expand"></div>';
    const scope = document.querySelector("body");

    var label = Vis.body.nodes[nodeId].options.properties.label;

    if ("topiclabel" in Vis.body.nodes[nodeId].options.properties) {
      var topiclabel = Vis.body.nodes[nodeId].options.properties.topiclabel;

      // var topicedam = Vis.body.nodes[nodeId].options.properties.topicedam;

      document.getElementById("topic").innerHTML = "";
      for (var i = 0; i < topiclabel.length; i++) {
        var buttonTopic = document.createElement("button");
        buttonTopic.className = "TopicButton";
        buttonTopic.innerText = topiclabel[i];
        buttonTopic.value = topiclabel[i];
        document.getElementById("topic").appendChild(buttonTopic);
      }
    }
    var buttonTopic = document.getElementsByClassName("TopicButton");
    for (var i = 0; i < buttonTopic.length; i++) {
      buttonTopic[i].addEventListener("click", function (buttonTopic) {
        addNodes(buttonTopic.srcElement.value, "", "Topic");
      });
    }

    document.getElementById("webpage").innerHTML =
      '<button onclick="window.open(&#34;https://openebench.bsc.es/tool/' +
      label +
      '&#34; , &#34;_blank&#34; )">Webpage</button>';

    var buttonCenter = document.createElement("button");
    buttonCenter.innerText = "Center";
    buttonCenter.addEventListener("click", function () {
      centerNode(name, nodeId);
    });
    document.getElementById("center").appendChild(buttonCenter);

    var buttonExpand = document.createElement("button");
    buttonExpand.innerText = "Expand";
    buttonExpand.addEventListener("click", function () {
      addNodes(name, nodeId, "Tool");
    });
    document.getElementById("expand").appendChild(buttonExpand);

    const normalizePozition = (mouseX, mouseY) => {
      // ? compute what is the mouse position relative to the container element (scope)
      let { left: scopeOffsetX, top: scopeOffsetY } =
        scope.getBoundingClientRect();

      scopeOffsetX = scopeOffsetX < 0 ? 0 : scopeOffsetX;
      scopeOffsetY = scopeOffsetY < 0 ? 0 : scopeOffsetY;

      const scopeX = mouseX - scopeOffsetX;
      const scopeY = mouseY - scopeOffsetY;

      // ? check if the element will go out of bounds
      const outOfBoundsOnX =
        scopeX + contextMenu.clientWidth > scope.clientWidth;

      const outOfBoundsOnY =
        scopeY + contextMenu.clientHeight > scope.clientHeight;

      let normalizedX = mouseX;
      let normalizedY = mouseY;

      // ? normalize on X
      if (outOfBoundsOnX) {
        normalizedX =
          scopeOffsetX + scope.clientWidth - contextMenu.clientWidth;
      }

      // ? normalize on Y
      if (outOfBoundsOnY) {
        normalizedY =
          scopeOffsetY + scope.clientHeight - contextMenu.clientHeight;
      }

      return { normalizedX, normalizedY };
    };

    scope.addEventListener("click", (event) => {
      // event.preventDefault();
      const { clientX: mouseX, clientY: mouseY } = event;

      const { normalizedX, normalizedY } = normalizePozition(mouseX, mouseY);

      contextMenu.classList.remove("visible");

      contextMenu.style.top = `${normalizedY}px`;
      contextMenu.style.left = `${normalizedX}px`;

      setTimeout(() => {
        contextMenu.classList.add("visible");
      });
    });

    scope.addEventListener("click", (e) => {
      // ? close the menu if the user clicks outside of it
      if (e.target.offsetParent !== contextMenu) {
        contextMenu.classList.remove("visible");
      }
    });
  }
}

/**
 * La función addLoadingTool oculta una pantalla de carga en la interfaz 
 * y realiza algunas configuraciones finales para preparar la visualización 
 * del gráfico o red. También detiene cualquier simulación que esté corriendo 
 * y ajusta algunos modos visuales.
 */
function addLoadingTool() {
  setTimeout(function () {
    clusterMode();
    addLegend();
  });
  Vis.stopSimulation();
  Vis.off("afterDrawing", addLoadingTool);
  // Vis.network.fit();
  Vis.stopSimulation();
  document.getElementById("loadingSpinner").style.display = "none";
  document.getElementById("loading").style.display = "none";
}

/**
 * La función waitAddTool establece un breve retraso para estabilizar la 
 * visualización de la red o gráfico en Vis y configura un evento para ejecutar 
 * addLoadingTool una vez que el gráfico esté completamente dibujado.
 */
function waitAddTool() {
  setTimeout(function () {
    Vis.stabilize(100);
    Vis.on("afterDrawing", addLoadingTool);
  });
}

/**
 * La función reset restablece completamente la visualización eliminando 
 * el gráfico actual, redibujándolo y limpiando elementos de la interfaz 
 * relacionados, como el menú de herramientas y la leyenda. Esto es útil 
 * para reiniciar el estado de la visualización y empezar de nuevo sin 
 * información ni elementos anteriores.
 */
function reset() {
  Vis.destroy();
  drawVis();
  removeAllToolsMenu();
  removeLegend();
}

/**
 * Este codigo agrega el botón de restablecimiento
 */
document.getElementById("reset").addEventListener("click", function () {
  removeAllTopicsMenu();
  reset();
});

const sta = document.getElementById("stabilize");

//Este codigo agrega el boton de estabilización.
// Stabilize the network
sta.addEventListener("click", () => {
  Vis.stopSimulation();
});