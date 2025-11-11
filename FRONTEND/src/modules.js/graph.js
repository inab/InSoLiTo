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
import CloseButton from "../images/xmark-solid-white.svg";

// Modules
import { addLegend, removeLegend, removeAllToolsMenu, removeAllTopicsMenu } from "./navBar";
import { appendAlert, showTopicsAdded, hideTopicsAdded, showToolsAdded, hideToolsAdded, hideLegend } from "../main";



// ------------------------------------------------------------ VARIABLES ------------------------------------------------------------ //

// Neovis.js options
let Vis;
let nodes;
let edges;
let firstSearchNoResult = false;



// ------------------------------------------------------------ FUNCTIONS ------------------------------------------------------------ //

// ------------------------------ Function-1 ------------------------------
/**
 * Draw the Vis.js network with the specified options. The network is
 * drawn on the element with id 'VisNetwork'.
 * @param {object} - The options for the network.
 */
const drawVis = () => {
  nodes = new vis.DataSet(); // the nodes of the graph
  edges = new vis.DataSet(); // the edges of the graph
  let container = $('#VisNetwork')[0]; // the element to draw the graph on
  let data = {
    nodes: nodes, // the nodes of the graph
    edges: edges, // the edges of the graph
  };
  let options = {
    // the layout options
    layout: {
      // the randomSeed is set to 34 to ensure the same layout every time the graph is drawn
      randomSeed: 34,
    },
    // the physics options
    physics: {
      // the forceAtlas2Based layout algorithm is used
      forceAtlas2Based: {
        // the gravitationalConstant is set to -200 to move the nodes away from each other
        gravitationalConstant: -200,
        // the springLength is set to 400 to make the nodes move away from each other
        springLength: 400,
        // the springConstant is set to 0.36 to control the speed of the nodes
        springConstant: 0.36,
        // the avoidOverlap is set to 1 to avoid overlapping nodes
        avoidOverlap: 1,
      },
      // the maxVelocity is set to 30 to control the speed of the nodes
      maxVelocity: 30,
      // the solver is set to forceAtlas2Based to use the forceAtlas2Based layout algorithm
      solver: "forceAtlas2Based",
      // the timestep is set to 1 to control the speed of the nodes
      timestep: 1,
      // the adaptiveTimestep is set to true to make the nodes move faster
      adaptiveTimestep: true,
      // the stabilization is enabled to make the nodes move smoothly
      stabilization: {
        enabled: true,
        iterations: 2000,
        updateInterval: 25,
        fit: true,
      },
    },
    // the interaction options
    interaction: {
      // the tooltipDelay is set to 200 to make the tooltips appear after 200 milliseconds
      tooltipDelay: 200,
      // the navigationButtons are enabled to allow the user to zoom in and out and move the graph
      navigationButtons: true,
    },
    // the nodes options
    nodes: {
      // the font size is set to 26 to make the labels of the nodes readable
      font: {
        size: 26,
        strokeWidth: 7,
      },
      // the scaling is not used
      scaling: {},
      // the shapeProperties is not used
      shapeProperties: {
        interpolation: false,
      },
    },
    // the edges options
    edges: {
      // the length is set to 200 to make the edges visible
      length: 200,
    },
  };
  // verify if librería vis.js is correctly loaded
  if (typeof vis === "undefined" || !vis.Network) {
    console.error("Vis.js library not loaded");
    return;
  }
  // create the network
  Vis = new vis.Network(container, data, options);
}



// ------------------------------ Function-2 ------------------------------
/**
 * Updates the nodes in the visualization by resetting the graph and
 * re-adding nodes based on the current state of the UI elements.
 */
const updateNodes = () => {
  // Initialize an empty dictionary to store the name of the node and
  // its information.
  let nameNodeDict = {};
  // Iterate over the classes of the buttons in the legend.
  ["ToolButton", "TopicButton"].forEach((className) => {
    // Get all the elements with the class name.
    let listLegend = document.querySelectorAll(`.${className}`);
    // Iterate over the elements and add the name of the node and its
    // information to the dictionary.
    Array.from(listLegend).forEach((element) => {
      let nameNode = element.textContent.trim();
      let nodeInformation = element.value || element.dataset.info;
      if (!nameNode || !nodeInformation) {
        return;
      }
      // Determine the type of node based on the class name.
      const typeNode = className === "ToolButton" ? "Tool" : "Topic";
      nameNodeDict[nameNode] = [nodeInformation, typeNode];
    });
  });
  // If the dictionary is empty, return.
  if (Object.keys(nameNodeDict).length === 0) {
    return;
  }
  // Reset the graph.
  resetVisualization();
  // Iterate over the dictionary and add the nodes to the graph.
  Object.entries(nameNodeDict).forEach(([nameNode, [nodeInformation, typeNode]]) => {
    addNodes(nameNode, nodeInformation, typeNode);
  });
}



// ------------------------------ Function-3 ------------------------------
/**
 * Returns a dictionary containing the clusters (communities) of the graph.
 * Each key in the dictionary is a community ID and the value is an object
 * with the following properties:
 * - count: the number of nodes in the community
 * - mTopic: the main topic of the community
 * - mLanguage: the main language of the community
 * - mOS: the main OS of the community
 * - tNodesDB: the total number of nodes in the database for the community
 * - color: the color of the community
 */
const returnClusters = () => {
  let dictClusters = {};
  if (!Vis || !Vis.body) {
    console.error("Vis or Vis.body is null or undefined");
    return dictClusters;
  }
  let net = Vis.body;
  let allNodes = net.nodeIndices;
  if (!Array.isArray(allNodes)) {
    return dictClusters;
  }
  // Iterate over all nodes in the graph and store their colors in the node data
  allNodes.forEach((node) => {
    let nodeData = net.nodes[node];
    if (!nodeData || !nodeData.options) {
      return;
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
  });
  // Iterate over the community data and add it to the clusters dictionary
  if (!Array.isArray(communityData)) {
    return dictClusters;
  }
  communityData.forEach((community) => {
    if (!community || typeof community === "undefined") {
      return;
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
  });
  return dictClusters;
}



// ------------------------------ Function-4 ------------------------------
/**
 * Stores the colors of the nodes in the graph for when the cluster mode is
 * disabled.
 *
 * This function is called when the cluster mode is disabled. It iterates
 * over all nodes in the graph and stores their colors in the node data.
 * The colors are stored in a nested object structure, with the original
 * colors being stored in the "colorcluster" property and the normal colors
 * being stored in the "colornormal" property.
 *
 * The function also checks if the node is a centered node (i.e. if it has
 * been centered by the user) and sets its normal colors accordingly.
 *
 * The function uses a timeout to ensure that it runs after the graph has
 * been updated.
 *
 * @function
 */
const storeClusterColor = () => {
  setTimeout(() => {
    // Get the current network object
    let net = Vis.body;
    if (!net || !net.nodeIndices) {
      console.error("Invalid network body structure");
      return;
    }
    // Get all nodes in the graph
    let allNodes = net.nodeIndices;
    // Get all the centered nodes
    let listLegend = $(".ToolButton");
    if (!listLegend || listLegend.length === 0) {
      console.error("Failed to get centered nodes");
    }
    let centeredNodes = [];
    listLegend.each(function () {
      centeredNodes.push($(this).val());
    });
    // Iterate over all nodes and store their colors
    allNodes.forEach((node) => {
      // Get the node data
      let nodeData = net.nodes[node];
      if (!nodeData || !nodeData.options || !nodeData.options.color) {
        console.error("Invalid node data structure");
        return;
      }
      // Store the original colors
      if (!nodeData.options.colorcluster) {
        nodeData.options.colorcluster = {
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
        };
      }
      // Store the normal colors
      if (!nodeData.options.colornormal) {
        nodeData.options.colornormal = {};
      }
      // Check if the node is a centered node
      if (centeredNodes.includes(node)) {
        nodeData.options.colornormal = {
          background: "#fbba7e",
          border: "#f99234",
          highlight: { background: "#fbba7e", border: "#f99234" },
          hover: { background: "#fbba7e", border: "#f99234" },
        };
      } else {
        // Set the normal colors based on the node type
        switch (nodeData.options.Neo4jLabel) {
          case "Tool":
            nodeData.options.colornormal = {
              background: "#add8e6",
              border: "#6bc5e3",
              highlight: { background: "#add8e6", border: "#6bc5e3" },
              hover: { background: "#add8e6", border: "#6bc5e3" },
            };
            break;
          case "Database":
            nodeData.options.colornormal = {
              background: "#b2e6ad",
              border: "#4ed442",
              highlight: { background: "#b2e6ad", border: "#4ed442" },
              hover: { background: "#b2e6ad", border: "#4ed442" },
            };
            break;
          default:
            nodeData.options.colornormal = {
              background: "#FB7E81",
              border: "#FA0A10",
              highlight: { background: "#FB7E81", border: "#FA0A10" },
              hover: { background: "#FB7E81", border: "#FA0A10" },
            };
        }
      }
    });
    // Update the graph with the new node colors
    nodes.update(allNodes.map(node => ({
      id: node,
      color: net.nodes[node].options.colornormal
    })));
  });
}



// ------------------------------ Function-5 ------------------------------
/**
 * Updates the colors of the nodes in the graph based on the chosen cluster
 * mode.
 *
 * If the cluster mode is "Cluster", the colors of the nodes are set to their
 * cluster colors. Otherwise, the colors of the nodes are set to their normal
 * colors.
 *
 * @return {Promise<void>}
 */
const clusterMode = () => {
  // Get the selected cluster mode radio button
  let optionRadio = document.querySelector(
    'input[name="cluster_mode"]:checked'
  );
  // Create an array to store the nodes that need to be updated
  let listChanges = [];
  let net = Vis.body;
  // Iterate over all nodes in the graph
  let allNodes = net.nodeIndices;
  allNodes.forEach((node) => {
    // Get the node data from the network body
    let nodeData = net.nodes[node];
    // Determine the color path based on the cluster mode
    let colorNodePath =
      optionRadio.value === "Cluster"
        ? nodeData.options.colorcluster
        : nodeData.options.colornormal;
    // Create an object to store the changes for the node
    let changeNode = {
      id: node,
      color: { ...colorNodePath }
    };
    // Add the changes to the list of changes
    listChanges.push(changeNode);
  });
  // If there are any changes, update the nodes
  if (listChanges.length > 0) {
    nodes.update(listChanges);
  }
}



// ------------------------------ Function-6 ------------------------------
/**
 * Handles the node selection event. When a node is selected, a context menu
 * is displayed with options to expand the node, center the node, or delete
 * the node.
 *
 * @param e1 {Object} The event object containing information about the
 *   selected nodes.
 */
const algo = () => {
  Vis.on("selectNode", (e1) => {
    if (e1 && e1.nodes && e1.nodes.length > 0) {
      menu(e1); // Display a context menu with options for the selected node
    }
  });
  Vis.on("deselectNode", () => {
    const contextMenu = $("#context-menu");
    if (contextMenu) {
      contextMenu.html(""); // Clear the context menu when all nodes are deselected
    }
  });
}



// ------------------------------ Function-7 ------------------------------
/**
 * Adds nodes and edges to the visualization.
 *
 * This function takes in arrays of node and edge data and adds them
 * to the network visualization. This is essential for updating the
 * visual representation of the network with new or modified elements.
 *
 * @param {Array} nodeDataArray - An array of node objects to be added to the visualization.
 * @param {Array} edgeDataArray - An array of edge objects to be added to the visualization.
 */
const createVisVisualization = (nodeDataArray, edgeDataArray) => {
  if (!nodes || !edges) {
    console.error("nodes or edges is null or undefined");
  }
  if (!Array.isArray(nodeDataArray)) {
    console.error("nodeDataArray is not a valid array");
  }
  if (!Array.isArray(edgeDataArray)) {
    console.error("edgeDataArray is not a valid array");
  }
  // Add the nodes to the network
  nodes.add(nodeDataArray);
  // Add the edges to the network
  edges.add(edgeDataArray);
}



// ------------------------------ Function-8 ------------------------------
/**
 * Sends a POST request to the specified URL with the specified data.
 *
 * This function is used to send a POST request to the specified URL with
 * the specified data. It returns a Promise that resolves to the response
 * from the server.
 *
 * @param {string} url - The URL to send the POST request to.
 * @param {object} data - The data to be sent with the POST request.
 * @return {Promise} A Promise that resolves to the response from the server.
 */
const postData = async (url = "", data = {}) => {
  // Validating the URL and data
  if (!url) {
    console.error("url is null or empty");
  }
  if (!data) {
    console.error("data is null or empty");
  }
  try {
    // Sending the POST request with the data
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
    // Check if the response is okay
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    // Return the parsed JSON from the response
    return response.json();
  } catch (error) {
    console.log(`Error in postData: ${error.message}`);
    // TODO change the alert link
    appendAlert('While sending the data an error has occurred. Try again with the same parameters and if the problem persists, try it in a few minutes.', 'danger')
    return Promise.reject(error);
  }
}



// ------------------------------ Function-9 ------------------------------
/**
 * Updates the visualization with data from a Cypher query.
 *
 * This function sends a Cypher query to the server, receives the resulting
 * nodes and edges, and updates the graph visualization by adding new nodes
 * and edges if they don't already exist.
 *
 * @param {string} cypherQuery - The Cypher query to execute on the server.
 */
const updateWithCypher = (cypherQuery) => {
  // Prepare the input data for the POST request
  if (!cypherQuery) {
    console.error("cypherQuery is null or empty");
  }
  let inputData = {
    statements: [
      {
        statement: cypherQuery,
        resultDataContents: ["graph"],
      },
    ],
  };
  // Send the Cypher query to the server
  return postData(sampleConfig.serverUrl, inputData)
    .then((datainput) => {
      let edgeDataArray = []; // Array to store new edge data
      let nodeDataArray = []; // Array to store new node data
      const idNodesSet = new Set(); // Set to track existing node IDs
      if (Vis.body && Vis.body.nodeIndices) {
        Vis.body.nodeIndices.forEach(idNodesSet.add, idNodesSet);
      }
      const idEdgesSet = new Set(); // Set to track existing edge IDs
      if (Vis.body && Vis.body.edgeIndices) {
        Vis.body.edgeIndices.forEach(idEdgesSet.add, idEdgesSet);
      }
      // Iterate over the results of the Cypher query
      datainput.results[0].data.forEach((element) => {
        // Ensure the element has valid data for nodes
        if (!element || !element.graph || !element.graph.nodes) {
          throw new Error("element.graph is null or not a valid array");
        }
        // Process nodes from the query result
        element.graph.nodes.forEach((nodeElement) => {
          // Ensure the node is valid
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
              // Determine the image to use based on the node label
              let imageLabel;
              if (nodeElement.labels[0] === "Tool") {
                imageLabel = ToolImage;
              } else if (nodeElement.labels[0] === "Database") {
                imageLabel = DatabaseImage;
              }
              // Add node data to the array
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
        // Ensure the element has valid data for relationships
        if (!element.graph.relationships) {
          throw new Error("element.graph.relationships is null or not a valid array");
        }
        // Process edges from the query result
        element.graph.relationships.forEach((edgeElement) => {
          // Ensure the edge is valid
          if (!edgeElement || !edgeElement.id) {
            throw new Error("edgeElement is null or not a valid object");
          }
          if (!idEdgesSet.has(edgeElement.id)) {
            idEdgesSet.add(edgeElement.id);
            if (edgeElement.type === "METAOCCUR_ALL") {
              // Add edge data to the array
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
      // Update the visualization with the new nodes and edges
      createVisVisualization(nodeDataArray, edgeDataArray);
    });
}



// ------------------------------ Function-10 ------------------------------
/**
 * Add nodes to the graph based on the given name and type
 * @param {string} nameNode - The name of the node to add
 * @param {string} idNode - The ID of the node to add
 * @param {string} nodeType - The type of the node to add (Tool or Topic)
 */
const addNodesGraph = async (nameNode, idNode, nodeType) => {
  // Check if articles should be displayed
  let displayArticles = $("#displayArticles").prop("checked");
  // Get the selected type of edges
  let typeOfEdges = $('input[name="typeOfEdges"]:checked');
  // Get the minimum value for the occurrence slider
  let cMin = $("#occurAmount").val();
  // The maximum value of occurrences is fixed at 100
  let cMax = 100;
  // Get the minimum and maximum values for the year slider
  let yMin = $("#yearAmount").val().substr(0, $("#yearAmount").val().indexOf("-") - 1);
  let yMax = $("#yearAmount").val().substr(
    $("#yearAmount").val().indexOf("-") + 2,
    $("#yearAmount").val().length
  );
  let cypherQuery = "";
  // Build the Cypher query based on the node type and edge type
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
  let nodesBeforeQuery = nodes.getIds();
  try {
    await updateWithCypher(cypherQuery);
  } catch (error) {
    console.log(`Error in addNodesGraph: ${error.message}`);
    appendAlert('While loading a node an error has occurred. Try again with the same parameters and if the problem persists, try it in a few minutes.', 'danger')
    return;
  }
  let nodesAfter = nodes.getIds();
  let addedNodes = nodesAfter.filter((id) => !nodesBeforeQuery.includes(id));
  // Show the loading screen
  $("#reset").prop("disabled", true);
  $("#stabilize").prop("disabled", true);
  $("#tooltopic_autocomplete").prop("disabled", true);
  $("#displayArticles").prop("disabled", true);
  $("#allYearsEdges").prop("disabled", true);
  $("#EdgesByYear").prop("disabled", true);
  $("#initial-screen").addClass("hidden");
  $("#cluster").prop("disabled", true);
  $("#normal").prop("disabled", true);
  $("#occur-slider-range").slider("disable");
  $("#occurAmount").prop("disabled", true);
  $("#year-slider-range").slider("disable");
  $("#yearAmount").prop("disabled", true);
  $(".ToolButton").prop("disabled", true);
  $(".TopicButton").prop("disabled", true);
  const LoadingImg = $("#loadingSpinner");
  LoadingImg.attr('src', LoadingIcon);
  LoadingImg.removeClass("hidden");
  LoadingImg.addClass("loading");
  const list = $("#loading");
  list.removeClass("hidden");
  list.addClass("loading");
  const loadingText = $("#loadingText");
  loadingText.html(`🔍 Searching data about <strong>${nameNode}</strong> <span class="dots"></span>`);
  loadingText.removeClass("hidden");
  loadingText.addClass("loading");
  const VisNetwork = $("#VisNetwork");
  VisNetwork.addClass("hidden");
  const resetPage = $("#resetPage");
  resetPage.addClass("hidden");
  setTimeout(() => {
    list.addClass("hidden");
    $("#reset").prop("disabled", false);
    $("#stabilize").prop("disabled", false);
    $("#tooltopic_autocomplete").prop("disabled", false);
    $("#displayArticles").prop("disabled", false);
    $("#allYearsEdges").prop("disabled", false);
    $("#EdgesByYear").prop("disabled", false);
    $("#cluster").prop("disabled", false);
    $("#normal").prop("disabled", false);
    $("#occur-slider-range").slider("enable");
    $("#occurAmount").prop("disabled", false);
    $("#year-slider-range").slider("enable");
    $("#yearAmount").prop("disabled", false);
    $(".ToolButton").prop("disabled", false);
    $(".TopicButton").prop("disabled", false);
  }, 15000);
  await new Promise((r) => setTimeout(r, 15000));
  // Check if no new nodes were added
  if (nodes.length === 0 || nodes.length === nodesBeforeQuery) {
    appendAlert('No results found. Try again!', 'info');
    list.attr("class", "hidden");
    VisNetwork.removeClass("hidden");
    firstSearchNoResult = true;
    return;
  }
  firstSearchNoResult = false;
  // Add the appropriate label to the menu based on node type
  if (nodeType === "Topic") {
    addTopicLabelMenu(nameNode, addedNodes);
  } else {
    addToolLabelMenu(nameNode, idNode);
  }
  // Execute additional logic if nodes were found
  if (nodes.length > 0) {
    algo();
    await new Promise(() => {
      storeClusterColor();
      waitAddTool();
      setTimeout(() => {
        list.attr("class", "hidden");
        VisNetwork.removeClass("hidden");
      }, 1000);
    });
  }
}



// ------------------------------ Function-11 ------------------------------
/**
 * Adds nodes to the graph visualization.
 *
 * This function adds nodes to the graph visualization by making a Cypher query
 * to the server and processing the results. It also handles the case where
 * the node is already in the menu and should not be added again.
 *
 * @param {string} nameNode - The name of the node to add.
 * @param {number} idNode - The ID of the node to add.
 * @param {string} nodeType - The type of node to add. Can be "Tool" or "Topic".
 */
const addNodes = (nameNode, idNode, nodeType) => {
  if (!nameNode || !nodeType) {
    console.error("nameNode or nodeType is null or empty");
  }
  let contextMenu = $("#context-menu");
  if (!contextMenu) {
    console.error("contextMenu is null or empty");
  }
  contextMenu.html("");
  let list = $(".delete");
  // Check if the node is already in the menu
  let isInMenu = false;
  Array.prototype.forEach.call(list, (tool) => {
    if (tool.textContent === nameNode) {
      isInMenu = true;
    }
  });
  if (!isInMenu) {
    // Add the node to the graph if it is not already in the menu
    addNodesGraph(nameNode, idNode, nodeType);
  }
}



// ------------------------------ Function-12 ------------------------------
/**
 * Centers a node in the graph visualization.
 *
 * This function resets the graph visualization, removes all topics from the menu,
 * and adds the node to the graph visualization by calling addNodes.
 *
 * @param {string} name - The name of the node to center.
 * @param {number} idNode - The ID of the node to center.
 */
const centerNode = (name, idNode) => {
  if (!name || !idNode) {
    console.error("name or idNode is null or empty");
  }
  resetVisualization();
  removeAllTopicsMenu();
  addNodes(name, idNode, "Tool");
}



// ------------------------------ Function-13 ------------------------------
/**
 * Adds a topic label to the topics menu if it does not already exist.
 *
 * This function checks if a topic with the specified name already exists
 * in the menu. If it does not, it creates a new topic button element and
 * appends it to the topics list.
 *
 * @param {string} NameTopic - The name of the topic to add to the menu.
 * @param {number[]} addedNodeIds - The IDs of the nodes that were added to the graph.
 */
const addTopicLabelMenu = (NameTopic, addedNodeIds) => {
  let topicButtonElements = $(".TopicButton");
  let found = false;
  topicButtonElements.each(function () {
    if ($(this).text().trim() === NameTopic.trim()) {
      found = true;
      return false;
    }
  });

  if (firstSearchNoResult) return;
  if (found) {
    appendAlert('Topic: ' + NameTopic + ' is already in the graph', 'info');
    return;
  }

  if (addedNodeIds.length === 0) {
    appendAlert('No connected nodes for topic: ' + NameTopic, 'info');
    return;
  }

  showTopicsAdded();
  let buttonTopic = $("<button>");
  buttonTopic.addClass("btn btn-primary w-100 my-1 pe-4 TopicButton");

  /**
   * This HTML structure is used to create a new topic button element.
   * The close-icon is an SVG icon that is used to remove the topic from the menu.
   * The name-topic is the name of the topic that is displayed in the menu.
   */
  buttonTopic.html(`
    <img class="close-icon pt-1 me-3" src="${CloseButton}"/>
    <div class="name-topic">${NameTopic}</div>
  `);

  buttonTopic.val(addedNodeIds.join(","));

  let topicsList = $("#topics-list");

  topicsList.append(buttonTopic);

  if ($("#topics-tools-list").hasClass("hidden")) {
    $("#topics-tools-list").removeClass("hidden");
  }
  // (Re)select all topic buttons and attach the click event handler.
  topicButtonElements = $(".TopicButton");
  topicButtonElements.off("click").on("click", (e) => {
    /**
     * This function is called when the topic button is clicked.
     * It removes the topic from the menu and deletes the nodes that are connected
     * to the topic from the graph.
     */
    let idTopicStr = e.currentTarget.value;
    let idTopicArray = idTopicStr.split(',').map(id => id.trim());
    $(e.currentTarget).remove();
    let ConnectedNodes = [];
    idTopicArray.forEach(id => {
      let nodesConnected = Vis.getConnectedNodes(id);
      if (Array.isArray(nodesConnected)) {
        ConnectedNodes = ConnectedNodes.concat(nodesConnected);
      }
    });
    let UnconnectedNodes = [];
    ConnectedNodes.forEach((node) => {
      if (Vis.getConnectedEdges(node).length === 1) {
        UnconnectedNodes.push(node);
      }
    });
    Vis.selectNodes(idTopicArray.concat(UnconnectedNodes));
    Vis.deleteSelected();
    let graphNodes = Vis.body.nodeIndices;
    graphNodes.forEach((node) => {
      if (Vis.getConnectedNodes(node).length === 0) {
        Vis.selectNodes([node]);
        Vis.deleteSelected();
      }
    });
    addLegend();
    if ($(".TopicButton").length === 0) {
      hideTopicsAdded();
      if ($(".ToolButton").length === 0) {
        // No topics and no tools - redirect to home
        removeAllTopicsMenu();
        resetVisualization();
        $("#topics-tools-list").addClass("hidden");
        $("#initial-screen").removeClass("hidden");
        $("#VisNetwork").addClass("hidden");
        $("#resetPage").removeClass("hidden");
        $("#reset").prop("disabled", true);
        $("#stabilize").prop("disabled", true);
      }
    }
  });
}



// ------------------------------ Function-14 ------------------------------
/**
 * Adds a tool label to the tools menu.
 *
 * This function creates a new button element for the tool label and appends
 * it to the tools list. It also adds an event listener to the button to remove
 * it from the menu when clicked. If the tool is removed, it also deletes the 
 * connected nodes from the graph.
 *
 * @param {string} NameTopic - The name of the tool to add to the menu.
 * @param {number} idNode - The ID of the node to add to the menu.
 */
const addToolLabelMenu = (NameTopic, idNode) => {
  // Ensure idNode is a trimmed string
  idNode = String(idNode).trim();
  // Check if the tool is already in the menu
  let toolButtonElements = $(".ToolButton");
  let found = false;
  toolButtonElements.each(function () {
    let currentText = $(this).find(".name-topic").text().trim();
    if (currentText === NameTopic.trim()) {
      found = true;
      return false; // Exit the loop early if found
    }
  });
  if (firstSearchNoResult) return;
  // If the tool is found, log and exit
  if (found) {
    appendAlert('Tool: ' + NameTopic + ' is already in the graph', 'info');
    return;
  }
  // Check if the node has connected nodes; if not, exit
  if (!idNode || Vis.getConnectedNodes(idNode).length === 0) {
    appendAlert('No connected nodes for tool: ' + NameTopic, 'info');
    return;
  }
  // Show the tools added section
  showToolsAdded();
  // Create the new tool button element
  let buttonTool = $("<button>");
  buttonTool.addClass("btn btn-primary ToolButton w-100 my-1");
  buttonTool.val(idNode);
  buttonTool.html(`
    <img class="close-icon pt-1" src="${CloseButton}"/>
    <div class="name-topic">${NameTopic}</div>
  `);
  // Append the button to the tools list
  let toolsList = $("#tools-list");
  toolsList.append(buttonTool);
  if($("#topics-tools-list").hasClass("hidden")) {
    $("#topics-tools-list").removeClass("hidden");
  }
  // Add an event listener to the tool buttons for removal
  $(".ToolButton").off("click").on("click", function (e) {
    // Get the ID of the tool to remove
    let IdTool = e.currentTarget.value;
    // Remove the button from the menu
    let buttonElement = $(e.currentTarget).closest(".ToolButton");
    if (buttonElement.length) {
      buttonElement.remove();
    }
    // Get connected nodes and determine which are unconnected
    let ConnectedNodes = Vis.getConnectedNodes(IdTool);
    let UnconnectedNodes = ConnectedNodes.filter(
      (node) => Vis.getConnectedEdges(node).length === 1
    );
    // Filter valid nodes that exist in the graph
    const validNodes = [IdTool].concat(UnconnectedNodes).filter(node => Vis.body.data.nodes.get(node));
    // Select and delete the nodes if any are valid
    if (validNodes.length > 0) {
      Vis.selectNodes(validNodes);
      Vis.deleteSelected();
    }
    // Check and remove any orphaned nodes
    let graphNodes = Vis.body.nodeIndices;
    graphNodes.forEach((node) => {
      if (Vis.getConnectedNodes(node).length === 0) {
        Vis.selectNodes([node]);
        Vis.deleteSelected();
      }
    });
    // Update the legend and hide the tools section if empty
    addLegend();
    if ($(".ToolButton").length === 0) {
      hideToolsAdded();
      if ($(".TopicButton").length === 0) {
        // No topics and no tools - redirect to home
        removeAllTopicsMenu();
        resetVisualization();
        $("#topics-tools-list").addClass("hidden");
        $("#initial-screen").removeClass("hidden");
        $("#VisNetwork").addClass("hidden");
        $("#resetPage").removeClass("hidden");
        $("#reset").prop("disabled", true);
        $("#stabilize").prop("disabled", true);
      }
    }
  });
}



// ------------------------------ Function-15 ------------------------------
/**
 * This function creates a context menu when a node is clicked on the graph.
 * The context menu has the following options:
 * - Name of the node
 * - List of topics the node is associated with
 * - Webpage of the node
 * - Center the node on the graph
 * - Expand the node
 *
 * @param {Object} e1 - The event object containing the node that was clicked
 */
const menu = (e1) => {
  if (e1.nodes.length !== 1) {
    return;
  }
  let nodeId = e1.nodes[0];
  if (Vis.body.nodes[nodeId].options.Neo4jLabel !== "Tool") {
    return;
  }
  let name = Vis.body.nodes[nodeId].options.properties.name;
  // Get the context menu element
  const contextMenu = $("#context-menu");
  if (!contextMenu || contextMenu.length !== 1) {
    console.error("contextMenu is null or empty");
    return;
  }
  // Set the content of the context menu
  contextMenu.html(
    `<div class="item" id="nameTool">${name}</div>
    <div class="topicmenu" id="topic"></div>
    <div class="item" id="webpage"></div>
    <div class="item" id="center"></div>
    <div class="item" id="expand"></div>`
  );
  // Add the list of topics the node is associated with
  let label = Vis.body.nodes[nodeId].options.properties.label;
  if (!label) {
    console.error("label is null or empty");
    return;
  }
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
  // Add the event listener to each topic button
  $(".TopicButton").each(function () {
    $(this).on("click", () => {
      let topicId = Vis.body.nodes[nodeId].options.properties.topicId;
      addNodes($(this).val(), topicId, "Topic");
    });
  });
  // Add the webpage button
  $("#webpage").html(
    `<button onclick="window.open('https://openebench.bsc.es/tool/${label}', '_blank')">Webpage</button>`
  );
  // Add the center button
  let buttonCenter = $("<button></button>");
  buttonCenter.text("Center");
  buttonCenter.on("click", () => {
    centerNode(name, nodeId);
  });
  $("#center").append(buttonCenter);
  // Add the expand button
  let buttonExpand = $("<button>");
  buttonExpand.text("Expand");
  buttonExpand.on("click", () => {
    addNodes(name, nodeId, "Tool");
  });
  $("#expand").append(buttonExpand);
  // Function to normalize the position of the context menu
  const normalizePosition = (mouseX, mouseY) => {
    const scope = $("body")[0];
    const scopeRect = scope.getBoundingClientRect();
    const scopeOffsetX = scopeRect.left >= 0 ? scopeRect.left : 0;
    const scopeOffsetY = scopeRect.top >= 0 ? scopeRect.top : 0;
    const scopeX = mouseX - scopeOffsetX;
    const scopeY = mouseY - scopeOffsetY;
    const outOfBoundsOnX =
      scopeX + contextMenu[0].clientWidth > scopeRect.width;
    const outOfBoundsOnY =
      scopeY + contextMenu[0].clientHeight > scopeRect.height;
    let normalizedX = mouseX;
    let normalizedY = mouseY;
    if (outOfBoundsOnX) {
      normalizedX = scopeOffsetX + scopeRect.width - contextMenu[0].clientWidth;
    }
    if (outOfBoundsOnY) {
      normalizedY = scopeOffsetY + scopeRect.height - contextMenu[0].clientHeight;
    }
    return { normalizedX, normalizedY };
  };
  // Add the event listener to the document to display the context menu
  $(document).on("click", (e) => {
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
  // Add the event listener to the document to hide the context menu
  $(document).on("click", (e) => {
    if (!$(e.target).closest("#context-menu").length) {
      contextMenu.removeClass("visible");
    }
  });
};



// ------------------------------ Function-16 ------------------------------
/**
 * Function to handle the loading process for adding tools to the graph.
 * This function is triggered after the graph drawing process is complete.
 * It modifies the cluster mode, updates the legend, and stops the simulation.
 */
const addLoadingTool = () => {
  if (!clusterMode || !addLegend || !Vis.stopSimulation || !Vis.off) {
    console.error("Some required functions are missing.");
    return;
  }
  // Delay execution to ensure graph is fully drawn before proceeding
  setTimeout(() => {
    clusterMode(); // Apply the cluster mode settings
    addLegend(); // Update the legend in the graph
  });
  // Stop the graph's physics simulation
  Vis.stopSimulation();
  // Remove this function from the 'afterDrawing' event listener
  Vis.off("afterDrawing", addLoadingTool);
  // Hide the loading spinner and overlay
  $("#loadingSpinner").attr("class", "hidden");
  $("#loading").attr("class", "hidden");
}



// ------------------------------ Function-17 ------------------------------
/**
 * Function to handle the waiting process for adding tools to the graph.
 * This function is triggered after the graph drawing process is complete.
 * It waits for the graph to stabilize before calling the next function.
 */
const waitAddTool = () => {
  if (!Vis) {
    console.error("Vis is null or undefined.");
    return;
  }
  // Add a delay to ensure the graph has fully drawn before proceeding
  setTimeout(() => {
    // Stabilize the graph to ensure a smooth transition
    Vis.stabilize(100);
    // Add the next function to the 'afterDrawing' event listener
    Vis.on("afterDrawing", addLoadingTool);
  }, 1000);
}



// ------------------------------ Function-18 ------------------------------
/**
 * Resets the graph visualization by destroying and recreating it from scratch.
 * This function is useful for resetting the graph after modifying the UI elements.
 */
const resetVisualization = () => {
  if (!Vis) {
    console.error("Vis is null or undefined.");
  }
  // Destroy the current graph visualization
  Vis.destroy();
  // Recreate the graph visualization from scratch
  drawVis();
  // Remove all nodes from the graph
  removeAllToolsMenu();
  removeLegend();
  hideTopicsAdded();
  hideToolsAdded();
  hideLegend();
}



// ------------------------------------------------------------ EXPORTS ------------------------------------------------------------ //

export { Vis, drawVis, updateNodes, returnClusters, clusterMode, addNodes, resetVisualization };