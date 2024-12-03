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

// Neovis.js options
let Vis;
let nodes;
let edges;

function drawVis() {
  nodes = new vis.DataSet();
  edges = new vis.DataSet();
  let container = $('#VisNetwork')[0];
  let data = {
    nodes: nodes,
    edges: edges,
  };
  let options = {
    layout: {
      randomSeed: 34,
    },
    physics: {
      forceAtlas2Based: {
        gravitationalConstant: -200,
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
        interpolation: false,
      },
    },
    edges: {
      length: 200,
    },
  };
  Vis = new vis.Network(container, data, options);
}

$("#openbtn").on("click", () => {
  actionSidebar();
});

function removeLoadingPage() {
  let loadingPage = $("#enter-webpage");
  loadingPage.remove();
}

function createHomePage() {
  let homePage = $("#inital-screen");
  let divHomePage = $("<div></div>");
  let imgHomePage = $('<img>', {
    class: "imgHomePage",
    alt: "InSoLiTo Logo",
    src: logoInSoLiTo
  });
  divHomePage.append(imgHomePage);
  homePage.prepend(divHomePage);
}

$(function () {
  createHomePage();
  removeLoadingPage();
  drawVis();
  actionSidebar();
  sliderRangeFunction();
  initAutocomplete(ToolTopicData, addNodes, ToolImage, DatabaseImage, TopicImage);
});

let YearCanvas = $("#YearCanvas")[0];

let YearBarchart = new Barchart({
  canvas: YearCanvas,
  padding: 0,
  data: YearData,
  colors: ["#0b579f"],
});

YearBarchart.draw();

let OccurCanvas = $("#OccurCanvas")[0];

let OccurBarchart = new Barchart({
  canvas: OccurCanvas,
  padding: 0,
  data: OccurData,
  colors: ["#0b579f"],
});

OccurBarchart.draw();

function updateNodes() {
  let nameNodeDict = {};
  ["ToolButton", "topicDiv"].forEach((className) => {
    let listLegend = $(`.${className}`);
    for (let i = 0; i < listLegend.length; i++) {
      let nameNode = listLegend[i].textContent;
      let nodeInformation = listLegend[i].value;
      const typeNode = className === "ToolButton" ? "Tool" : "Topic";
      nameNodeDict[nameNode] = [nodeInformation, typeNode];
    }
  });
  reset();
  for (const [nameNode, listNode] of Object.entries(nameNodeDict)) {
    addNodes(nameNode, listNode[0], listNode[1]);
  }
}

export function returnClusters() {
  let net = Vis.body;
  let allNodes = net.nodeIndices;
  let dictClusters = {};

  allNodes.forEach((node) => {
    let commId = net.nodes[node].options.group;
    let colorId = net.nodes[node].options.color.background;
    if (dictClusters.hasOwnProperty(commId)) {
      dictClusters[commId].count += 1;
    }
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

function storeClusterColor() {
  setTimeout(function () {
    let net = Vis.body;
    let allNodes = net.nodeIndices;
    let listLegend = $(".ToolButton")[0];
    let centeredNodes = [];
    for (let i = 0; i < listLegend.length; i++) {
      centeredNodes.push(listLegend[i].value);
    }
    allNodes.forEach((node) => {
      let objCluster = {
        colorcluster: {
          background: null,
          border: null,
          highlight: { background: null, border: null },
          hover: { background: null, border: null },
        },
      };
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
      let objNormal = {
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
      if (centeredNodes.includes(node)) {
        objNormal.colornormal.background = "#fbba7e";
        objNormal.colornormal.border = "#f99234";
        objNormal.colornormal.highlight.background = "#fbba7e";
        objNormal.colornormal.highlight.border = "#f99234";
        objNormal.colornormal.hover.background = "#fbba7e";
        objNormal.colornormal.hover.border = "#f99234";
      }
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

function clusterMode() {
  let optionRadio = document.querySelector(
    'input[name="cluster_mode"]:checked'
  );
  let listChanges = [];
  let net = Vis.body;
  let allNodes = net.nodeIndices;
  allNodes.forEach((node) => {
    let colorNodePath = optionRadio.value === "Cluster" ? net.nodes[node].options.colorcluster : net.nodes[node].options.colornormal;
    let changeNode = {
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
  nodes.update(listChanges);
}

$("input[type=radio][name=cluster_mode]").change(function () {
  clusterMode();
  addLegend();
});

$("input[type=checkbox][name=displayArticles]").change(function () {
  updateNodes();
});

$("#allYearsEdges, #EdgesByYear").change(function () {
  updateNodes();
  let optionEdges = $("input[name=typeOfEdges]:checked");
  if (optionEdges.val() === "allYearsEdges") {
    $("#yearColumn").css('display', "none");
  } else {
    $("#yearColumn").css('display', "block");
  }
});

function algo() {
  Vis.on("selectNode", (e1) => {
    menu(e1);
  });
  Vis.on("deselectNode", () => {
    $("#context-menu").html("");
  });
}

function removeAllToolsMenu() {
  $("#tools-list").html("");
}

function removeAllTopicsMenu() {
  $("#topics-list").html("");
}

function createVisVisualization(nodeDataArray, edgeDataArray) {
  nodes.add(nodeDataArray);
  edges.add(edgeDataArray);
}

async function postData(url = "", data = {}) {
  const response = await fetch(url, {
    method: "POST",
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
    body: JSON.stringify(data),
  });
  return response.json();
}

function updateWithCypher(cypherQuery) {
  let inputData = {
    statements: [
      {
        statement: cypherQuery,
        resultDataContents: ["graph"],
      },
    ],
  };

  postData(sampleConfig.serverUrl, inputData).then((datainput) => {
    let edgeDataArray = [];
    let nodeDataArray = [];
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
            let imageLabel;
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

async function addNodesGraph(nameNode, idNode, nodeType) {
  let displayArticles = $("#displayArticles").checked;
  displayArticles = $("#displayArticles").checked;
  let typeOfEdges = $('input[name="typeOfEdges"]:checked');
  let cMin = $("#occurAmount")
    .val()
    .substr(0, $("#occurAmount").val().indexOf("-") - 1);
  let cMax = $("#occurAmount")
    .val()
    .substr(
      $("#occurAmount").val().indexOf("-") + 2,
      $("#occurAmount").val().length
    );
  let yMin = $("#yearAmount")
    .val()
    .substr(0, $("#yearAmount").val().indexOf("-") - 1);
  let yMax = $("#yearAmount")
    .val()
    .substr(
      $("#yearAmount").val().indexOf("-") + 2,
      $("#yearAmount").val().length
    );
  let cypherQuery = "";
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
  let nodesBeforeQuery = nodes.length;
  updateWithCypher(cypherQuery);
  $("#inital-screen").css('display', "none");
  const LoadingImg = $("#loadingSpinner");
  LoadingImg.attr('src', LoadingIcon);
  LoadingImg.css('display', "block");
  const list = $("#loading");
  list.css('display', "block");
  await new Promise((r) => setTimeout(r, 15000));
  if (nodes.length === 0 || nodes.length === nodesBeforeQuery) {
    alert("No results found. Try again!");
    list.css('display', "none");
  }
  if (nodeType === "Topic") {
    addTopicLabelMenu(nameNode);
  } else {
    addToolLabelMenu(nameNode, idNode);
  }
  algo();
  await new Promise(() => {
    storeClusterColor();
    waitAddTool();
  });
}

function addNodes(nameNode, idNode, nodeType) {
  let contextMenu = $("#context-menu");
  contextMenu.html("");
  let list = $(".delete");
  let isInMenu = false;
  Array.prototype.forEach.call(list, function (tool) {
    if (tool.textContent === nameNode) {
      isInMenu = true;
    }
  });
  if (isInMenu === false) {
    addNodesGraph(nameNode, idNode, nodeType);
  }
}

function centerNode(name, idNode) {
  reset();
  removeAllTopicsMenu();
  addNodes(name, idNode, "Tool");
}

function addTopicLabelMenu(NameTopic) {
  let topicDivElements = $(".topicDiv")[0];
  for (let i = 0; i < topicDivElements.length; i++) {
    if (topicDivElements[i].innerText === NameTopic) {
      return;
    }
  }
  var divTopic = $("<div>");
  divTopic.class("topicDiv");
  divTopic.text(NameTopic);
  $("#topics-list").append(divTopic);
}

function addToolLabelMenu(NameTopic, idNode) {
  let buttonTool = $("<button>");
  buttonTool.addClass("ToolButton");
  buttonTool.val(idNode);
  buttonTool.html(
    '<img class="close-icon" src="' +
    CloseButton +
    '"/>' +
    '<div class="name-topic">' +
    NameTopic +
    "</div>");
  $("#tools-list").append(buttonTool);
  buttonTool = $(".ToolButton");
  for (let i = 0; i < buttonTool.length; i++) {
    buttonTool[i].addEventListener("click", function (e) {
      let IdTool = e.currentTarget.value;
      e.currentTarget.parentNode.removeChild(e.currentTarget);
      let ConnectedNodes = Vis.getConnectedNodes(IdTool);
      let UnconnectedNodes = [];
      ConnectedNodes.forEach((node) => {
        if (Vis.getConnectedEdges(node).length === 1) {
          UnconnectedNodes.push(node);
        }
      });
      Vis.selectNodes([IdTool].concat(UnconnectedNodes));
      Vis.deleteSelected();
      let graphNodes = Vis.body.nodeIndices;
      graphNodes.forEach((node) => {
        if (Vis.getConnectedNodes(node).length === 0) {
          Vis.selectNodes([node]);
          Vis.deleteSelected();
        }
      });
      addLegend();
    });
  }
}

function menu(e1) {
  if (e1.nodes.length === 1) {
    let nodeId = e1.nodes[0];
    if (Vis.body.nodes[nodeId].options.Neo4jLabel === "Publication") {
      return;
    }
    let name = Vis.body.nodes[nodeId].options.properties.name;
    const contextMenu = $("#context-menu");
    contextMenu.html(
      '<div class="item" id="nameTool">' +
      name +
      '</div><div class="topicmenu" id="topic"></div><div class="item" id = "webpage"></div><div class="item" id="center"></div><div class="item" id="expand"></div>');
    const scope = $("body");
    let label = Vis.body.nodes[nodeId].options.properties.label;
    if ("topiclabel" in Vis.body.nodes[nodeId].options.properties) {
      let topiclabel = Vis.body.nodes[nodeId].options.properties.topiclabel;
      $("#topic").html("");
      for (let i = 0; i < topiclabel.length; i++) {
        let buttonTopic = $("<button></button>");
        buttonTopic.class("TopicButton");
        buttonTopic.text(topiclabel[i]);
        buttonTopic.val(topiclabel[i]);
        $("#topic").append(buttonTopic);
      }
    }
    let buttonTopic = $(".TopicButton");
    for (let i = 0; i < buttonTopic.length; i++) {
      buttonTopic[i].addEventListener("click", function (buttonTopic) {
        addNodes(buttonTopic.target.value, "", "Topic");
      });
    }
    $("#webpage").html(
      '<button onclick="window.open(&#34;https://openebench.bsc.es/tool/' +
      label +
      '&#34; , &#34;_blank&#34; )">Webpage</button>');
    let buttonCenter = $("<button></button>");
    buttonCenter.text("Center");
    buttonCenter.on("click", function () {
      centerNode(name, nodeId);
    });
    document.$("#center").append(buttonCenter);
    let buttonExpand = $("<button>");
    buttonExpand.text("Expand");
    buttonExpand.on("click", function () {
      addNodes(name, nodeId, "Tool");
    });
    document.$("#expand").append(buttonExpand);
    const normalizePozition = (mouseX, mouseY) => {
      let { left: scopeOffsetX, top: scopeOffsetY } =
        scope.getBoundingClientRect();
      scopeOffsetX = scopeOffsetX < 0 ? 0 : scopeOffsetX;
      scopeOffsetY = scopeOffsetY < 0 ? 0 : scopeOffsetY;
      const scopeX = mouseX - scopeOffsetX;
      const scopeY = mouseY - scopeOffsetY;
      const outOfBoundsOnX =
        scopeX + contextMenu.clientWidth > scope.clientWidth;
      const outOfBoundsOnY =
        scopeY + contextMenu.clientHeight > scope.clientHeight;
      let normalizedX = mouseX;
      let normalizedY = mouseY;
      if (outOfBoundsOnX) {
        normalizedX =
          scopeOffsetX + scope.clientWidth - contextMenu.clientWidth;
      }
      if (outOfBoundsOnY) {
        normalizedY =
          scopeOffsetY + scope.clientHeight - contextMenu.clientHeight;
      }
      return { normalizedX, normalizedY };
    };
    scope.on("click", (event) => {
      const { clientX: mouseX, clientY: mouseY } = event;
      const { normalizedX, normalizedY } = normalizePozition(mouseX, mouseY);
      contextMenu.removeClass("visible");
      contextMenu.css({
        "top": `${normalizedY}px`,
        "left": `${normalizedX}px`
      });
      setTimeout(() => {
        contextMenu.addClass("visible");
      });
    });
    scope.on("click", (e) => {
      if (e.target.offsetParent !== contextMenu) {
        contextMenu.removeClass("visible");
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
  Vis.stopSimulation();
  $("#loadingSpinner").css('display', "none");
  $("#loading").css('display', "none");
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

$("#reset").on("click", function () {
  removeAllTopicsMenu();
  reset();
});

$("#stabilize").on("click", () => {
  Vis.stopSimulation();
});