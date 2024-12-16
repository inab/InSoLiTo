// ------------------------------------------------------------ IMPORTS ------------------------------------------------------------ //

// Dependencies
import $ from "jquery";
import "jquery-ui/ui/core";
import "jquery-ui/ui/widgets/slider.js";
import "jquery-ui/ui/widgets/autocomplete.js";
import vis from "vis-network/dist/vis-network.min.js";

// JSON
import sampleConfig from "../config.json";
import communityData from "../../../DB/CommunityData.json";

// Images
import ToolImage from "../images/tool_centered_sm.png";
import PaperImage from "../images/paper_centered_sm.png";
import DatabaseImage from "../images/database_centered_sm.png";
import LoadingIcon from "../images/spinner-solid.svg";
import CloseButton from "../images/xmark-solid.svg";

// Modules
import { addLegend, removeLegend, removeAllToolsMenu, removeAllTopicsMenu } from "./navBar";

// Neovis.js options
let Vis;
let nodes;
let edges;



// ------------------------------------------------------------ FUNCTIONS ------------------------------------------------------------ //

// ------------------------------ Function-1 ------------------------------
function drawVis() {
  try {
    nodes = new vis.DataSet();
    edges = new vis.DataSet();
    let container = $('#VisNetwork')[0];
    if (!container) {
      throw new Error("VisNetwork container not found in DOM");
    }
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
    if (typeof vis === "undefined" || !vis.Network) {
      throw new Error("vis.js library not loaded");
    }
    Vis = new vis.Network(container, data, options);
  } catch (error) {
    console.log("Error in drawVis:", error.message);
    alert("TODO issue #11");
  }
}



// ------------------------------ Function-2 ------------------------------
function updateNodes() {
  try {
    let nameNodeDict = {};
    ["ToolButton", "topicDiv"].forEach((className) => {
      let listLegend = $(`.${className}`);
      if (!listLegend || listLegend.length === 0) {
        throw new Error(`No elements found for class: ${className}`);
      }
      for (let i = 0; i < listLegend.length; i++) {
        let nameNode = listLegend[i].textContent;
        let nodeInformation = listLegend[i].value;
        if (!nameNode || !nodeInformation) {
          throw new Error(`Invalid data for node: ${nameNode}`);
        }
        const typeNode = className === "ToolButton" ? "Tool" : "Topic";
        nameNodeDict[nameNode] = [nodeInformation, typeNode];
      }
    });
    reset();
    for (const [nameNode, listNode] of Object.entries(nameNodeDict)) {
      addNodes(nameNode, listNode[0], listNode[1]);
    }
  } catch (error) {
    console.log("Error in updateNodes:", error.message);
    alert("TODO issue #11");
  }
}



// ------------------------------ Function-3 ------------------------------
function returnClusters() {
  let dictClusters = {};
  try {
    if (!Vis || !Vis.body) {
      throw new Error("Vis.js library not loaded");
    }
    let net = Vis.body;
    let allNodes = net.nodeIndices;
    if (!Array.isArray(allNodes)) {
      throw new Error("Error in allNodes");
    }
    allNodes.forEach((node) => {
      try {
        let nodeData = net.nodes[node];
        if (!nodeData || !nodeData.options) {
          throw new Error("Error in nodeData");
        }
        let commId = net.nodes[node].options.group;
        let colorId = net.nodes[node].options.color.background;
        if (dictClusters.hasOwnProperty(commId)) {
          dictClusters[commId].count += 1;
        } else {
          dictClusters[commId] = {
            count: 1,
            mTopic: "Undefined",
            mLanguage: "Undefinded",
            mOS: "Undefined",
            tNodesDB: 0,
            color: colorId,
          };
        }
      } catch (nodeError) {
        console.log(`Error in node ${node}:`, nodeError.message);
        alert("TODO issue #11");
      }
    });
    if (!Array.isArray(communityData)) {
      throw new Error("Error in communityData");
    }
    communityData.forEach((community) => {
      try {
        if (!community || typeof community === "undefined") {
          throw new Error("Error in community");
        }
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
      } catch (communityError) {
        console.log(`Error in community ${community.id}:`, communityError.message);
        alert("TODO issue #11");
      }
    });
  } catch (error) {
    console.log("Error in returnClusters:", error.message);
    alert("TODO issue #11");
  }
  return dictClusters;
}



function storeClusterColor() {
  setTimeout(function () {
    try {
      let net = Vis.body;
      if (!net || !net.nodeIndices) {
        throw new Error("Invalid network body structure");
      }
      let allNodes = net.nodeIndices;
      let listLegend = $(".ToolButton");
      if (!listLegend || listLegend.length === 0) {
        throw new Error("ToolButton list is empty or not found");
      }
      let centeredNodes = [];
      listLegend.each(function () {
        centeredNodes.push($(this).val());
      });
      allNodes.forEach((node) => {
        try {
          let nodeData = net.nodes[node];
          if (!nodeData || !nodeData.options || !nodeData.options.color) {
            throw new Error(`Invalid node data for node ${node}`);
          }
          let objCluster = {
            colorcluster: {
              background: nodeData.options.color.background,
              border: nodeData.options.color.border,
              highlight: {
                background: nodeData.options.color.highlight.background,
                border: nodeData.options.color.highlight.border,
              },
              hover: {
                background: nodeData.options.color.hover.background,
                border: nodeData.options.color.hover.border,
              },
            },
          };
          let objNormal = {
            colornormal: {
              background: null,
              border: null,
              highlight: { background: null, border: null },
              hover: { background: null, border: null },
            },
          };
          switch (nodeData.options.Neo4jLabel) {
            case "Tool":
              objNormal.colornormal = {
                background: "#add8e6",
                border: "#6bc5e3",
                highlight: { background: "#add8e6", border: "#6bc5e3" },
                hover: { background: "#add8e6", border: "#6bc5e3" },
              };
              break;
            case "Database":
              objNormal.colornormal = {
                background: "#b2e6ad",
                border: "#4ed442",
                highlight: { background: "#b2e6ad", border: "#4ed442" },
                hover: { background: "#b2e6ad", border: "#4ed442" },
              };
              break;
            default:
              objNormal.colornormal = {
                background: "#FB7E81",
                border: "#FA0A10",
                highlight: { background: "#FB7E81", border: "#FA0A10" },
                hover: { background: "#FB7E81", border: "#FA0A10" },
              };
          }
          if (centeredNodes.includes(node)) {
            objNormal.colornormal = {
              background: "#fbba7e",
              border: "#f99234",
              highlight: { background: "#fbba7e", border: "#f99234" },
              hover: { background: "#fbba7e", border: "#f99234" },
            };
          }
          nodeData.options = Object.assign(nodeData.options, objCluster, objNormal);
        } catch (nodeError) {
          console.log(`Error processing node ${node}:`, nodeError.message);
          alert("TODO issue #11");
        }
      });
    } catch (error) {
      console.log("Error in storeClusterColor:", error.message);
      alert("TODO issue #11");
    }
  });
}



// ------------------------------ Function-5 ------------------------------
function clusterMode() {
  try {
    let optionRadio = document.querySelector(
      'input[name="cluster_mode"]:checked'
    );
    if (!optionRadio) {
      throw new Error("No cluster mode selected");
    }
    let listChanges = [];
    let net = Vis.body;
    if (!net || !net.nodeIndices || !net.nodes) {
      throw new Error("Invalid network body structure");
    }
    let allNodes = net.nodeIndices;
    allNodes.forEach((node) => {
      try {
        let nodeData = net.nodes[node];
        if (!nodeData || !nodeData.options) {
          throw new Error(`Invalid node data for node ${node}`);
        }
        let colorNodePath = optionRadio.value === "Cluster" ? nodeData.options.colorcluster : nodeData.options.colornormal;
        if (!colorNodePath) {
          throw new Error(`Color data missing for node ${node}`);
        }
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
      } catch (nodeError) {
        console.log(`Error processing node ${node}:`, nodeError.message);
        alert("TODO issue #11");
      }
    });
    if (listChanges.length > 0) {
      nodes.update(listChanges);
    }
  } catch (error) {
    console.log("Error in clusterMode:", error.message);
    alert("TODO issue #11");
  }
}



// ------------------------------ Function-6 ------------------------------
function algo() {
  Vis.on("selectNode", (e1) => {
    if (e1 && e1.nodes && e1.nodes.length > 0) {
      menu(e1);
    }
  });
  Vis.on("deselectNode", () => {
    const contextMenu = $("#context-menu");
    if (contextMenu) {
      contextMenu.html("");
    }
  });
}



// ------------------------------ Function-7 ------------------------------
function createVisVisualization(nodeDataArray, edgeDataArray) {
  try {
    if (!nodes || !edges) {
      throw new Error("Vis.js library not loaded");
    }
    if (!Array.isArray(nodeDataArray)) {
      throw new Error("nodeDataArray is not a valid array");
    }
    if (!Array.isArray(edgeDataArray)) {
      throw new Error("edgeDataArray is not a valid array");
    }
    nodes.add(nodeDataArray);
    edges.add(edgeDataArray);
  } catch (error) {
    console.log("Error in createVisVisualization:", error.message);
    alert("TODO issue #11");
  }
}



// ------------------------------ Function-8 ------------------------------
async function postData(url = "", data = {}) {
  if (!url) {
    throw new Error("url is null or empty");
  }
  if (!data) {
    throw new Error("data is null or empty");
  }
  try {
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
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  } catch (error) {
    console.log("Error in postData:", error.message);
    alert("TODO issue #11");
    return Promise.reject(error);
  }
}



// ------------------------------ Function-9 ------------------------------
function updateWithCypher(cypherQuery) {
  if (!cypherQuery) {
    throw new Error("cypherQuery is null or empty");
  }
  let inputData = {
    statements: [
      {
        statement: cypherQuery,
        resultDataContents: ["graph"],
      },
    ],
  };
  postData(sampleConfig.serverUrl, inputData)
    .then((datainput) => {
      if (!datainput || !Array.isArray(datainput.results)) {
        throw new Error("datainput is null or not a valid array");
      }
      let edgeDataArray = [];
      let nodeDataArray = [];
      const idNodesSet = new Set();
      if (Vis.body && Vis.body.nodeIndices) {
        Vis.body.nodeIndices.forEach(idNodesSet.add, idNodesSet);
      }
      const idEdgesSet = new Set();
      if (Vis.body && Vis.body.edgeIndices) {
        Vis.body.edgeIndices.forEach(idEdgesSet.add, idEdgesSet);
      }
      datainput.results[0].data.forEach((element) => {
        try {
          if (!element || !element.graph || !element.graph.nodes) {
            throw new Error("element.graph is null or not a valid array");
          }
          element.graph.nodes.forEach((nodeElement) => {
            if (!nodeElement || !nodeElement.id) {
              throw new Error("nodeElement is null or not a valid object");
            }
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
          if (!element.graph.relationships) {
            throw new Error("element.graph.relationships is null or not a valid array");
          }
          element.graph.relationships.forEach((edgeElement) => {
            if (!edgeElement || !edgeElement.id) {
              throw new Error("edgeElement is null or not a valid object");
            }
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
        } catch (err) {
          console.log("Error in updateWithCypher:", err.message);
          alert("TODO issue #11");
        }
      });
      createVisVisualization(nodeDataArray, edgeDataArray);
    })
    .catch((error) => {
      console.log("Error in updateWithCypher:", error.message);
      alert("TODO issue #11");
    });
}



// ------------------------------ Function-10 ------------------------------
async function addNodesGraph(nameNode, idNode, nodeType) {
  let displayArticles = $("#displayArticles").prop("checked");
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
    if (typeOfEdges.val() === "allYearsEdges") {
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
      if (typeOfEdges.val() === "allYearsEdges") {
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
      if (typeOfEdges.val() === "allYearsEdges") {
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
  try {
    updateWithCypher(cypherQuery);
  } catch (error) {
    console.log("Error in addNodesGraph:", error.message);
    alert("TODO issue #11");
    return;
  }
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
  if (nodes.length > 0) {
    algo();
    await new Promise(() => {
      storeClusterColor();
      waitAddTool();
    });
  }
}



// ------------------------------ Function-11 ------------------------------
function addNodes(nameNode, idNode, nodeType) {
  if (!nameNode || !nodeType) {
    throw new Error("nameNode or nodeType is null or empty");
  }
  let contextMenu = $("#context-menu");
  if (!contextMenu) {
    throw new Error("context-menu is null or not found");
  }
  contextMenu.html("");
  let list = $(".delete");
  if (!list || list.length === 0) {
    throw new Error("No elements found for class: delete");
  }
  let isInMenu = false;
  Array.prototype.forEach.call(list, function (tool) {
    if (!tool) {
      throw new Error("tool is null or empty");
    }
    if (tool.textContent === nameNode) {
      isInMenu = true;
    }
  });
  if (!isInMenu) {
    addNodesGraph(nameNode, idNode, nodeType);
  }
}



// ------------------------------ Function-12 ------------------------------
function centerNode(name, idNode) {
  if (!name || !idNode) {
    throw new Error("name or idNode is null or empty");
  }
  reset();
  removeAllTopicsMenu();
  addNodes(name, idNode, "Tool");
}



// ------------------------------ Function-13 ------------------------------
function addTopicLabelMenu(NameTopic) {
  if (!NameTopic) {
    throw new Error("NameTopic is null or empty");
  }
  let topicDivElements = $(".topicDiv");
  if (!topicDivElements) {
    throw new Error("No elements found for class: topicDiv");
  }
  let found = false;
  for (let i = 0; i < topicDivElements.length; i++) {
    if (!topicDivElements[i]) {
      throw new Error("topicDivElements[" + i + "] is null");
    }
    if (topicDivElements[i].innerText === NameTopic) {
      found = true;
      break;
    }
  }
  if (!found) {
    let divTopic = $("<div>");
    if (!divTopic) {
      throw new Error("divTopic is null");
    }
    divTopic.addClass("topicDiv");
    divTopic.text(NameTopic);
    let topicsList = $("#topics-list");
    if (!topicsList) {
      throw new Error("No element found for id: topics-list");
    }
    topicsList.append(divTopic);
  }
}



// ------------------------------ Function-14 ------------------------------
function addToolLabelMenu(NameTopic, idNode) {
  try {
    if (!NameTopic || !idNode) {
      throw new Error("NameTopic or idNode is null or empty");
    }
    let buttonTool = $("<button>");
    if (!buttonTool) {
      throw new Error("Failed to create button element");
    }
    buttonTool.addClass("ToolButton");
    buttonTool.val(idNode);
    buttonTool.html(
      '<img class="close-icon" src="' +
      CloseButton +
      '"/>' +
      '<div class="name-topic">' +
      NameTopic +
      "</div>"
    );
    let toolsList = $("#tools-list");
    if (!toolsList) {
      throw new Error("No element found for id: tools-list");
    }
    toolsList.append(buttonTool);
    buttonTool = $(".ToolButton");
    if (!buttonTool || buttonTool.length === 0) {
      throw new Error("No elements found for class: ToolButton");
    }
    buttonTool.each(function () {
      $(this).on("click", function (e) {
        try {
          let IdTool = e.currentTarget.value;
          if (!IdTool) {
            throw new Error("IdTool is null or empty");
          }
          e.currentTarget.parentNode.removeChild(e.currentTarget);
          let ConnectedNodes = Vis.getConnectedNodes(IdTool);
          if (!Array.isArray(ConnectedNodes)) {
            throw new Error("ConnectedNodes is not an array");
          }
          let UnconnectedNodes = [];
          ConnectedNodes.forEach((node) => {
            if (Vis.getConnectedEdges(node).length === 1) {
              UnconnectedNodes.push(node);
            }
          });
          Vis.selectNodes([IdTool].concat(UnconnectedNodes));
          Vis.deleteSelected();
          let graphNodes = Vis.body.nodeIndices;
          if (!Array.isArray(graphNodes)) {
            throw new Error("Error in graphNodes");
          }
          graphNodes.forEach((node) => {
            if (Vis.getConnectedNodes(node).length === 0) {
              Vis.selectNodes([node]);
              Vis.deleteSelected();
            }
          });
          addLegend();
        } catch (toolButtonError) {
          console.log("Error in ToolButton click handler:", toolButtonError.message);
          alert("TODO issue #11");
        }
      });
    });
  } catch (error) {
    console.log("Error in addToolLabelMenu:", error.message);
    alert("TODO issue #11");
  }
}



// ------------------------------ Function-15 ------------------------------
function menu(e1) {
  if (e1.nodes.length === 1) {
    let nodeId = e1.nodes[0];
    if (Vis.body.nodes[nodeId].options.Neo4jLabel === "Publication") {
      return;
    }
    let name = Vis.body.nodes[nodeId].options.properties.name;
    const contextMenu = $("#context-menu");
    contextMenu.html(
      '<div class="item" id="nameTool">' + name + '</div>' +
      '<div class="topicmenu" id="topic"></div>' +
      '<div class="item" id="webpage"></div>' +
      '<div class="item" id="center"></div>' +
      '<div class="item" id="expand"></div>'
    );
    let label = Vis.body.nodes[nodeId].options.properties.label;
    if ("topiclabel" in Vis.body.nodes[nodeId].options.properties) {
      let topiclabel = Vis.body.nodes[nodeId].options.properties.topiclabel;
      $("#topic").html("");
      for (let i = 0; i < topiclabel.length; i++) {
        let buttonTopic = $("<button></button>");
        buttonTopic.addClass("TopicButton");
        buttonTopic.text(topiclabel[i]);
        buttonTopic.val(topiclabel[i]);
        $("#topic").append(buttonTopic);
      }
    }
    $(".TopicButton").each(function () {
      $(this).on("click", function () {
        addNodes($(this).val(), "", "Topic");
      });
    });
    $("#webpage").html(
      `<button onclick="window.open('https://openebench.bsc.es/tool/${label}', '_blank')">Webpage</button>`
    );
    let buttonCenter = $("<button></button>");
    buttonCenter.text("Center");
    buttonCenter.on("click", function () {
      centerNode(name, nodeId);
    });
    $("#center").append(buttonCenter);
    let buttonExpand = $("<button>");
    buttonExpand.text("Expand");
    buttonExpand.on("click", function () {
      addNodes(name, nodeId, "Tool");
    });
    $("#expand").append(buttonExpand);
    const normalizePosition = (mouseX, mouseY) => {
      let scope = $("body")[0];
      let { left: scopeOffsetX, top: scopeOffsetY } = scope.getBoundingClientRect();
      scopeOffsetX = scopeOffsetX < 0 ? 0 : scopeOffsetX;
      scopeOffsetY = scopeOffsetY < 0 ? 0 : scopeOffsetY;
      const scopeX = mouseX - scopeOffsetX;
      const scopeY = mouseY - scopeOffsetY;
      const outOfBoundsOnX = scopeX + contextMenu[0].clientWidth > scope.clientWidth;
      const outOfBoundsOnY = scopeY + contextMenu[0].clientHeight > scope.clientHeight;
      let normalizedX = mouseX;
      let normalizedY = mouseY;
      if (outOfBoundsOnX) {
        normalizedX = scopeOffsetX + scope.clientWidth - contextMenu[0].clientWidth;
      }
      if (outOfBoundsOnY) {
        normalizedY = scopeOffsetY + scope.clientHeight - contextMenu[0].clientHeight;
      }
      return { normalizedX, normalizedY };
    };
    $(document).on("click", function (e) {
      const { clientX: mouseX, clientY: mouseY } = e;
      const { normalizedX, normalizedY } = normalizePosition(mouseX, mouseY);
      contextMenu.removeClass("visible");
      contextMenu.css({
        "top": `${normalizedY}px`,
        "left": `${normalizedX}px`
      });
      setTimeout(() => {
        contextMenu.addClass("visible");
      }, 0);
    });
    $(document).on("click", function (e) {
      if (e.target.offsetParent !== contextMenu[0]) {
        contextMenu.removeClass("visible");
      }
    });
  }
}



// ------------------------------ Function-16 ------------------------------
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



// ------------------------------ Function-17 ------------------------------
function waitAddTool() {
  setTimeout(function () {
    Vis.stabilize(100);
    Vis.on("afterDrawing", addLoadingTool);
  });
}



// ------------------------------ Function-18 ------------------------------
function reset() {
  Vis.destroy();
  drawVis();
  removeAllToolsMenu();
  removeLegend();
}



// ------------------------------------------------------------ EXPORTS ------------------------------------------------------------ //

export { Vis, drawVis, updateNodes, returnClusters, clusterMode, addNodes, reset };