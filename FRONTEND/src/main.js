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

// JSON
import sampleConfig from "./config.json";
import OccurData from "../../DB/RelationshipSliderData.json";
import YearData from "../../DB/YearSliderData.json";
import ToolTopicData from "../../DB/ToolTopicAutocomplete.json";
import communityData from "../../DB/CommunityData.json";

// Images
import ToolImage from "./images/tool_centered_sm.png";
import PaperImage from "./images/paper_centered_sm.png";
import DatabaseImage from "./images/database_centered_sm.png";
import TopicImage from "./images/topic_centered_sm.png";
import CloseButton from "./images/xmark-solid.svg";
import LoadingIcon from "./images/spinner-solid.svg";
import logoInSoLiTo from "./images/logo_InSoLiTo.png";

// Modules
import { actionSidebar, Barchart, sliderRangeFunction, removeLegend, addLegend, initAutocomplete } from "./modules.js/navBar";
import { drawVis, Vis, nodes, edges } from "./modules.js/graph";


var navButton = document.getElementById("openbtn");
navButton.addEventListener("click", () => {
  actionSidebar();
});

function removeLoadingPage() {
  var loadingPage = document.getElementById("enter-webpage");
  loadingPage.parentElement.removeChild(loadingPage);
}

function createHomePage() {
  var homePage = document.getElementById("inital-screen");
  var divHomePage = document.createElement("div");
  var imgHomePage = document.createElement("img");
  imgHomePage.src = logoInSoLiTo;
  imgHomePage.className = "imgHomePageeee";
  imgHomePage.alt = "InSoLiTo Logo";
  divHomePage.appendChild(imgHomePage);
  homePage.insertBefore(divHomePage, homePage.firstChild);
}

$(function () {
  createHomePage();
  removeLoadingPage();
  drawVis();
  actionSidebar();
  sliderRangeFunction();
  initAutocomplete(ToolTopicData, addNodes, ToolImage, DatabaseImage, TopicImage);
});

var YearCanvas = document.getElementById("YearCanvas");
// Barchart options
var YearBarchart = new Barchart({
  canvas: YearCanvas,
  padding: 0,
  data: YearData,
  colors: ["#0b579f"],
});
// Initialize Barchart
YearBarchart.draw();

var OccurCanvas = document.getElementById("OccurCanvas");
// Barchart options
var OccurBarchart = new Barchart({
  canvas: OccurCanvas,
  padding: 0,
  data: OccurData,
  colors: ["#0b579f"],
});
// Initialize Barchart
OccurBarchart.draw();

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
// Function that retrieves the id and size of the communities from the graph
export function returnClusters() {
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

function createVisVisualization(nodeDataArray, edgeDataArray) {
  nodes.add(nodeDataArray);
  edges.add(edgeDataArray);
}

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

function updateWithCypher(cypherQuery) {
  var inputData = {
    statements: [
      {
        statement: cypherQuery,
        resultDataContents: ["graph"],
      },
    ],
  };

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
    createVisVisualization(nodeDataArray, edgeDataArray);
  });
}

// Run a Cypher query that will be displayed in the web
async function addNodesGraph(nameNode, idNode, nodeType) {
  var displayArticles = document.getElementById("displayArticles").checked;
  var displayArticles = document.getElementById("displayArticles").checked;
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
function addNodes(nameNode, idNode, nodeType) {
  // Remove menu
  var contextMenu = document.getElementById("context-menu");
  contextMenu.innerHTML = "";

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

function waitAddTool() {
  setTimeout(function () {
    Vis.stabilize(100);
    Vis.on("afterDrawing", addLoadingTool);
  });
}

function reset() {
  Vis.destroy();
  drawVis();
  removeAllToolsMenu();
  removeLegend();
}

document.getElementById("reset").addEventListener("click", function () {
  removeAllTopicsMenu();
  reset();
});

const sta = document.getElementById("stabilize");

// Stabilize the network
sta.addEventListener("click", () => {
  Vis.stopSimulation();
});
