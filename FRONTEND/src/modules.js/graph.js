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
import { appendAlert, showTopicsAdded, hideTopicsAdded, showToolsAdded, hideToolsAdded, hideLegend } from "../main";




// ------------------------------------------------------------ VARIABLES ------------------------------------------------------------ //

// Neovis.js options
let Vis;
let nodes;
let edges;



// ------------------------------------------------------------ FUNCTIONS ------------------------------------------------------------ //

// ------------------------------ Function-1 ------------------------------
/**
 * Draw the Vis.js network with the specified options. The network is
 * drawn on the element with id 'VisNetwork'.
 * @param {object} - The options for the network.
 */
const drawVis = () => {
  try {
    nodes = new vis.DataSet(); // the nodes of the graph
    edges = new vis.DataSet(); // the edges of the graph
    let container = $('#VisNetwork')[0]; // the element to draw the graph on
    if (!container) {
      throw new Error("VisNetwork container not found in DOM");
    }
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
      throw new Error("vis.js library not loaded");
    }
    // create the network
    Vis = new vis.Network(container, data, options);
  } catch (error) {
    console.log(`Error in drawVis: ${error.message}`);
    // TODO change the alert link
    appendAlert('While loading the graph library an error has occurred. Try again with the same parameters and if the problem persists try again in a few minutes. <a href="#" class="alert-link">Go back to home</a>.', 'danger')
  }
}

// ------------------------------ Function-2 ------------------------------
/**
 * Updates the nodes in the visualization by resetting the graph and
 * re-adding nodes based on the current state of the UI elements.
 */
const updateNodes = () => {
  try {
    // Dictionary to store node names and their associated information
    let nameNodeDict = {};
    // Iterate over each class name to gather node information
    ["ToolButton", "topicDiv"].forEach((className) => {
      let listLegend = $(`.${className}`);
      for (let i = 0; i < listLegend.length; i++) {
        let nameNode = listLegend[i].textContent; // Get the node name
        let nodeInformation = listLegend[i].value; // Get the node information
        if (!nameNode || !nodeInformation) {
          throw new Error(`Invalid data for node: ${nameNode}`);
        }
        const typeNode = className === "ToolButton" ? "Tool" : "Topic"; // Determine the node type
        nameNodeDict[nameNode] = [nodeInformation, typeNode]; // Store in the dictionary
      }
    });
    reset(); // Reset the graph to its initial state
    // Re-add nodes to the graph using the gathered information
    for (const [nameNode, listNode] of Object.entries(nameNodeDict)) {
      addNodes(nameNode, listNode[0], listNode[1]);
    }
  } catch (error) {
    console.log(`Error in updateNodes: ${error.message}`);
    // TODO change the alert link
    appendAlert('While updating the nodes an error has occurred. Try again with the same parameters and if the problem persists, try it in a few minutes. <a href="#" class="alert-link">Go back to home</a>.', 'danger')
  }
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
  try {
    if (!Vis || !Vis.body) {
      throw new Error("Vis.js library not loaded");
    }
    let net = Vis.body;
    let allNodes = net.nodeIndices;
    if (!Array.isArray(allNodes)) {
      throw new Error("Error in allNodes");
    }
    // Iterate over all nodes in the graph and store their colors in the node data
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
        console.log(`Error in node ${node}: ${nodeError.message}`);
        // TODO change the alert link
        appendAlert('While loading a node an error has occurred. Try again with the same parameters and if the problem persists, try it in a few minutes. <a href="#" class="alert-link">Go back to home</a>.', 'danger')
      }
    });
    // Iterate over the community data and add it to the clusters dictionary
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
        console.log(`Error in community ${community.id}: ${communityError.message}`);
        // TODO change the alert link
        appendAlert('While loading a community an error has occurred. Try again with the same parameters and if the problem persists, try it in a few minutes. <a href="#" class="alert-link">Go back to home</a>.', 'danger')
      }
    });
  } catch (error) {
    console.log(`Error in returnClusters: ${error.message}`);
    // TODO change the alert link
    appendAlert('While returning the clusters an error has occurred. Try again with the same parameters and if the problem persists, try it in a few minutes. <a href="#" class="alert-link">Go back to home</a>.', 'danger')
  }
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
 * @function
 */
const storeClusterColor = () => {
  setTimeout(() => {
    try {
      // Get the network body object
      let net = Vis.body;
      if (!net || !net.nodeIndices || !net.nodes) {
        console.warn("Invalid network body structure");
        return;
      }
      // Get the list of all nodes in the graph
      let allNodes = net.nodeIndices;
      // Get the list of centered tool nodes
      let listLegend = $(".ToolButton");
      if (!listLegend.length) {
        console.warn("ToolButton list is empty or not found");
      }
      let centeredNodes = [];
      listLegend.each(function () {
        centeredNodes.push($(this).val());
      });
      // Iterate over all nodes in the graph
      allNodes.forEach((node) => {
        try {
          // Get the node data from the network body
          let nodeData = net.nodes[node];
          if (!nodeData || !nodeData.options || !nodeData.options.color) {
            console.warn(`Invalid node data for node ${node}`);
            return;
          }
          // Create a nested object structure to store the colors
          let objCluster = {
            colorcluster: { ...nodeData.options.color }
          };
          let objNormal = {
            colornormal: {
              background: "#FB7E81",
              border: "#FA0A10",
              highlight: { background: "#FB7E81", border: "#FA0A10" },
              hover: { background: "#FB7E81", border: "#FA0A10" }
            }
          };
          // Set the normal colors based on the node type
          switch (nodeData.options.Neo4jLabel) {
            case "Tool":
              objNormal.colornormal = {
                background: "#add8e6",
                border: "#6bc5e3",
                highlight: { background: "#add8e6", border: "#6bc5e3" },
                hover: { background: "#add8e6", border: "#6bc5e3" }
              };
              break;
            case "Database":
              objNormal.colornormal = {
                background: "#b2e6ad",
                border: "#4ed442",
                highlight: { background: "#b2e6ad", border: "#4ed442" },
                hover: { background: "#b2e6ad", border: "#4ed442" }
              };
              break;
          }
          // Set the normal colors to orange if the node is a centered node
          if (centeredNodes.includes(node)) {
            objNormal.colornormal = {
              background: "#fbba7e",
              border: "#f99234",
              highlight: { background: "#fbba7e", border: "#f99234" },
              hover: { background: "#fbba7e", border: "#f99234" }
            };
          }
          // Update the node data with the new colors
          Object.assign(nodeData.options, objCluster, objNormal);
        } catch (nodeError) {
          console.warn(`Error processing node ${node}: ${nodeError.message}`);
        }
      });
    } catch (error) {
      console.error(`Error in storeClusterColor: ${error.message}`);
    }
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
  try {
    // Get the selected cluster mode radio button
    let optionRadio = document.querySelector(
      'input[name="cluster_mode"]:checked'
    );
    if (!optionRadio) {
      // Warn the user if no cluster mode is selected
      console.warn("No cluster mode selected");
      return;
    }
    // Create an array to store the nodes that need to be updated
    let listChanges = [];
    let net = Vis.body;
    if (!net || !net.nodeIndices || !net.nodes) {
      // Warn the user if the network body structure is invalid
      console.warn("Invalid network body structure");
      return;
    }
    // Iterate over all nodes in the graph
    let allNodes = net.nodeIndices;
    allNodes.forEach((node) => {
      try {
        // Get the node data from the network body
        let nodeData = net.nodes[node];
        if (!nodeData || !nodeData.options) {
          // Warn the user if the node data is invalid
          console.warn(`Invalid node data for node ${node}`);
          return;
        }
        // Determine the color path based on the cluster mode
        let colorNodePath =
          optionRadio.value === "Cluster"
            ? nodeData.options.colorcluster
            : nodeData.options.colornormal;
        if (!colorNodePath) {
          // Warn the user if the color data is missing
          console.warn(`Color data missing for node ${node}`);
          return;
        }
        // Create an object to store the changes for the node
        let changeNode = {
          id: node,
          color: { ...colorNodePath }
        };
        // Add the changes to the list of changes
        listChanges.push(changeNode);
      } catch (nodeError) {
        // Warn the user if an error occurs while processing a node
        console.warn(`Error processing node ${node}: ${nodeError.message}`);
      }
    });
    // If there are any changes, update the nodes
    if (listChanges.length > 0) {
      nodes.update(listChanges);
    }
  } catch (error) {
    // Log any errors that occur
    console.error("Error in clusterMode:", error.message);
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
    // Add the nodes to the network
    nodes.add(nodeDataArray);
    // Add the edges to the network
    edges.add(edgeDataArray);
  } catch (error) {
    console.log(`Error in createVisVisualization: ${error.message}`);
    // TODO change the alert link
    appendAlert('While creating the visualization an error has occurred. Try again with the same parameters and if the problem persists, try it in a few minutes. <a href="#" class="alert-link">Go back to home</a>.', 'danger')
  }
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
    throw new Error("url is null or empty");
  }
  if (!data) {
    throw new Error("data is null or empty");
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
    appendAlert('While sending the data an error has occurred. Try again with the same parameters and if the problem persists, try it in a few minutes. <a href="#" class="alert-link">Go back to home</a>.', 'danger')
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
  // Send the Cypher query to the server
  postData(sampleConfig.serverUrl, inputData)
    .then((datainput) => {
      // Validating the response
      if (!datainput || !Array.isArray(datainput.results)) {
        throw new Error("datainput is null or not a valid array");
      }
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
        try {
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
        } catch (err) {
          console.log(`Error in updateWithCypher: ${err.message}`);
          // TODO change the alert link
          appendAlert('While updating the visualization an error has occurred. Try again with the same parameters and if the problem persists, try it in a few minutes. <a href="#" class="alert-link">Go back to home</a>.', 'danger')
        }
      });
      // Update the visualization with the new nodes and edges
      createVisVisualization(nodeDataArray, edgeDataArray);
    })
    .catch((error) => {
      console.log(`Error in updateWithCypher: ${error.message}`);
      // TODO change the alert link
      appendAlert('While updating the visualization an error has occurred. Try again with the same parameters and if the problem persists, try it in a few minutes. <a href="#" class="alert-link">Go back to home</a>.', 'danger')
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
    console.log(`Error in addNodesGraph: ${error.message}`);
    // TODO change the alert link
    appendAlert('While loading a node an error has occurred. Try again with the same parameters and if the problem persists, try it in a few minutes. <a href="#" class="alert-link">Go back to home</a>.', 'danger')
    return;
  }
  $("#inital-screen").addClass("hidden");
  const LoadingImg = $("#loadingSpinner");
  LoadingImg.attr('src', LoadingIcon);
  LoadingImg.removeClass("hidden");
  LoadingImg.addClass("loading");
  const list = $("#loading");
  list.removeClass("hidden");
  list.addClass("loading");
  const loadingText = $("#loadingText");
  loadingText.text("Searching data...");
  loadingText.removeClass("hidden");
  loadingText.addClass("loading");
  const VisNetwork = $("#VisNetwork");
  VisNetwork.addClass("hidden");
  await new Promise((r) => setTimeout(r, 15000));
  if (nodes.length === 0 || nodes.length === nodesBeforeQuery) {
    console.log("No results found. Try again!");
    // TODO change the alert link
    appendAlert('No results found. Try again! <a href="#" class="alert-link">Go back to home</a>.', 'info');
    list.attr("class","hidden");
    VisNetwork.removeClass("hidden");
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
      setTimeout(() => {
        list.attr("class","hidden");
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
    throw new Error("nameNode or nodeType is null or empty");
  }
  let contextMenu = $("#context-menu");
  if (!contextMenu) {
    throw new Error("context-menu is null or not found");
  }
  contextMenu.html("");
  let list = $(".delete");
  // Check if the node is already in the menu
  let isInMenu = false;
  Array.prototype.forEach.call(list,(tool) => {
    if (!tool) {
      throw new Error("tool is null or empty");
    }
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
    throw new Error("name or idNode is null or empty");
  }
  reset();
  removeAllTopicsMenu();
  addNodes(name, idNode, "Tool");
}



// ------------------------------ Function-13 ------------------------------
/**
 * Adds a topic label to the topics menu if it does not already exist.
 *
 * This function checks if a topic with the specified name already exists
 * in the menu. If it does not, it creates a new topic div element and
 * appends it to the topics list.
 *
 * @param {string} NameTopic - The name of the topic to add to the menu.
 */
const addTopicLabelMenu = (NameTopic) => {
  if (!NameTopic) {
    throw new Error("NameTopic is null or empty");
  }
  // Toggle the visibility of the topics added element
  showTopicsAdded();
  // Get all existing topic div elements
  let topicDivElements = $(".topicDiv");
  if (!topicDivElements) {
    throw new Error("No elements found for class: topicDiv");
  }
  let found = false;
  // Check if the topic already exists in the menu
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
    // Create a new div element for the topic
    let divTopic = $("<div>");
    if (!divTopic) {
      throw new Error("divTopic is null");
    }
    divTopic.addClass("topicDiv");
    divTopic.text(NameTopic);
    // Append the new topic div to the topics list
    let topicsList = $("#topics-list");
    if (!topicsList) {
      throw new Error("No element found for id: topics-list");
    }
    topicsList.append(divTopic);
  }
  if ($(".topicDiv").length === 0) {
    hideTopicsAdded();
  }
}



// ------------------------------ Function-14 ------------------------------
/**
 * Adds a tool label to the tools menu.
 *
 * This function creates a new button element for the tool label and appends
 * it to the tools list. It also adds an event listener to the button to remove
 * it from the menu when clicked.
 *
 * @param {string} NameTopic - The name of the tool to add to the menu.
 * @param {number} idNode - The ID of the node to add to the menu.
 */
const addToolLabelMenu = (NameTopic, idNode) => {
  // Create a new button element for the tool label
  try {
    if (!NameTopic || !idNode) {
      throw new Error("NameTopic or idNode is null or empty");
    }
    let buttonTool = $("<button>");
    if (!buttonTool) {
      throw new Error("Failed to create button element");
    }
    showToolsAdded();
    buttonTool.addClass("btn btn-primary ToolButton w-100 my-1");
    buttonTool.val(idNode);
    buttonTool.html(
      `<img class="close-icon pt-1" src="${CloseButton}"/>
      <div class="name-topic">${NameTopic}</div>`
    );
    // Append the new button to the tools list
    let toolsList = $("#tools-list");
    if (!toolsList) {
      throw new Error("No element found for id: tools-list");
    }
    toolsList.append(buttonTool);
    // Get all the button elements in the tools list
    buttonTool = $(".ToolButton");
    if (!buttonTool || buttonTool.length === 0) {
      throw new Error("No elements found for class: ToolButton");
    }
    // Add an event listener to each button element to remove it from the menu when clicked
    buttonTool.each(function () {
      $(this).on("click", (e) => {
        try {
          // Get the ID of the node to remove from the menu
          let IdTool = e.currentTarget.value;
          if (!IdTool) {
            throw new Error("IdTool is null or empty");
          }
          // Remove the button element from the menu
          e.currentTarget.parentNode.removeChild(e.currentTarget);
          // Get all the connected nodes to the node to remove from the menu
          let ConnectedNodes = Vis.getConnectedNodes(IdTool);
          if (!Array.isArray(ConnectedNodes)) {
            throw new Error("ConnectedNodes is not an array");
          }
          // Filter out the nodes that have more than one edge connected
          let UnconnectedNodes = [];
          ConnectedNodes.forEach((node) => {
            if (Vis.getConnectedEdges(node).length === 1) {
              UnconnectedNodes.push(node);
            }
          });
          // Select the node to remove and its unconnected nodes
          Vis.selectNodes([IdTool].concat(UnconnectedNodes));
          // Delete the selected nodes from the graph
          Vis.deleteSelected();
          // Get all the remaining nodes in the graph
          let graphNodes = Vis.body.nodeIndices;
          if (!Array.isArray(graphNodes)) {
            throw new Error("Error in graphNodes");
          }
          // Filter out the nodes that have no edges connected
          graphNodes.forEach((node) => {
            if (Vis.getConnectedNodes(node).length === 0) {
              // Select the node and delete it from the graph
              Vis.selectNodes([node]);
              Vis.deleteSelected();
            }
          });
          // Add the legend to the graph again
          addLegend();
          if ($(".ToolButton").length === 0) {
            hideToolsAdded();
          }
        } catch (toolButtonError) {
          console.log(`Error in ToolButton click handler: ${toolButtonError.message}`);
          // TODO change the alert link
          appendAlert('While deleting the tool, an error has occurred. Please try again and if the problem persists try again in a few minutes. <a href="#" class="alert-link">Go back to home</a>.', 'danger')
        }
      });
    });
  } catch (error) {
    console.log(`Error in addToolLabelMenu: ${error.message}`);
    // TODO change the alert link
    appendAlert('While adding the tool, an error has occurred. Please try again and if the problem persists try again in a few minutes. <a href="#" class="alert-link">Go back to home</a>.', 'danger')
  }
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
  if (!Vis.body.nodes[nodeId]) {
    throw new Error("Error in menu: node not found");
  }
  if (Vis.body.nodes[nodeId].options.Neo4jLabel !== "Tool") {
    return;
  }
  let name = Vis.body.nodes[nodeId].options.properties.name;
  if (!name) {
    throw new Error("Error in menu: name is null or empty");
  }
  const contextMenu = $("#context-menu");
  if (!contextMenu || contextMenu.length !== 1) {
    throw new Error("Error in menu: context menu not found");
  }
  // Populate the context menu with different sections
  contextMenu.html(
    // Create a span element with the name of the node
    // Create a div element to hold the list of topics
    // Create a div element with the webpage of the node
    // Create a div element with the "Center" button
    // Create a div element with the "Expand" button
    `<div class="item" id="nameTool">${name}</div>
    <div class="topicmenu" id="topic"></div>
    <div class="item" id="webpage"></div>
    <div class="item" id="center"></div>
    <div class="item" id="expand"></div>`
  );
  let label = Vis.body.nodes[nodeId].options.properties.label;
  if (!label) {
    throw new Error("Error in menu: label is null or empty");
  }
  if ("topiclabel" in Vis.body.nodes[nodeId].options.properties) {
    let topiclabel = Vis.body.nodes[nodeId].options.properties.topiclabel;
    if (!Array.isArray(topiclabel)) {
      throw new Error("Error in menu: topiclabel is not an array");
    }
    $("#topic").html("");
    for (let i = 0; i < topiclabel.length; i++) {
      let buttonTopic = $("<button></button>");
      if (!buttonTopic) {
        throw new Error("Error in menu: buttonTopic is null");
      }
      buttonTopic.addClass("TopicButton");
      buttonTopic.text(topiclabel[i]);
      buttonTopic.val(topiclabel[i]);
      $("#topic").append(buttonTopic);
    }
  }
  // Add an event listener to each topic button to add the node to the graph
  $(".TopicButton").each(() => {
    $(this).on("click", () => {
      addNodes($(this).val(), "", "Topic");
    });
  });
  // Add the webpage of the node to the context menu
  $("#webpage").html(
    `<button onclick="window.open('https://openebench.bsc.es/tool/${label}', '_blank')">Webpage</button>`
  );
  // Add the "Center" button to the context menu
  let buttonCenter = $("<button></button>");
  if (!buttonCenter) {
    throw new Error("Error in menu: buttonCenter is null");
  }
  buttonCenter.text("Center");
  buttonCenter.on("click", () => {
    centerNode(name, nodeId);
  });
  $("#center").append(buttonCenter);
  // Add the "Expand" button to the context menu
  let buttonExpand = $("<button>");
  if (!buttonExpand) {
    throw new Error("Error in menu: buttonExpand is null");
  }
  buttonExpand.text("Expand");
  buttonExpand.on("click", () => {
    addNodes(name, nodeId, "Tool");
  });
  $("#expand").append(buttonExpand);
  // Function to normalize the position of the context menu
  const normalizePosition = (mouseX, mouseY) => {
    const scope = $("body")[0];
    if (!scope) {
      throw new Error("Error in menu: scope is null");
    }
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
  // Add an event listener to the document to show the context menu
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
  // Add an event listener to the document to hide the context menu
  $(document).on("click", (e) => {
    if (e.target.offsetParent !== contextMenu[0]) {
      contextMenu.removeClass("visible");
    }
  });
}



// ------------------------------ Function-16 ------------------------------
/**
 * Function to handle the loading process for adding tools to the graph.
 * This function is triggered after the graph drawing process is complete.
 * It modifies the cluster mode, updates the legend, and stops the simulation.
 */
const addLoadingTool = () => {
  if (!Vis) {
    throw new Error("Vis is null or undefined");
  }
  // Delay execution to ensure graph is fully drawn before proceeding
  setTimeout(() => {
    if (!clusterMode) {
      throw new Error("clusterMode is null or undefined");
    }
    clusterMode(); // Apply the cluster mode settings
    if (!addLegend) {
      throw new Error("addLegend is null or undefined");
    }
    addLegend(); // Update the legend in the graph
  });
  if (!Vis.stopSimulation) {
    throw new Error("Vis.stopSimulation is null or undefined");
  }
  Vis.stopSimulation(); // Stop the graph's physics simulation
  if (!Vis.off) {
    throw new Error("Vis.off is null or undefined");
  }
  // Remove this function from the 'afterDrawing' event listener
  Vis.off("afterDrawing", addLoadingTool);
  if (!Vis.stopSimulation) {
    throw new Error("Vis.stopSimulation is null or undefined");
  }
  Vis.stopSimulation(); // Stop the graph's physics simulation
  if (!$("#loadingSpinner")) {
    throw new Error("loadingSpinner is null or undefined");
  }
  // Hide the loading spinner
  $("#loadingSpinner").attr("class", "hidden");
  if (!$("#loading")) {
    throw new Error("loading is null or undefined");
  }
  // Hide the loading overlay
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
    throw new Error("Vis is null or undefined");
  }
  // Add a delay to ensure the graph has fully drawn before proceeding
  setTimeout(() => {
    if (!Vis.stabilize) {
      throw new Error("Vis.stabilize is null or undefined");
    }
    if (!Vis.on) {
      throw new Error("Vis.on is null or undefined");
    }
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
const reset = () => {
  try {
    if (!Vis) {
      throw new Error("Vis is null or undefined");
    }
    // Destroy the current graph visualization
    Vis.destroy();
    if (!drawVis) {
      throw new Error("drawVis is null or undefined");
    }
    // Recreate the graph visualization from scratch
    drawVis();
    if (!removeAllToolsMenu) {
      throw new Error("removeAllToolsMenu is null or undefined");
    }
    // Remove all nodes from the graph
    removeAllToolsMenu();
    if (!removeLegend) {
      throw new Error("removeLegend is null or undefined");
    }
    removeLegend();
    hideTopicsAdded();
    hideToolsAdded();
    hideLegend();
  } catch (error) {
    console.log(`Error in reset: ${error.message}`);
    // TODO change the alert link
    appendAlert('While resetting the visualization an error has occurred! Please try again and if the problem persists try again in a few minutes. <a href="#" class="alert-link">Go back to home</a>.', 'warning')
  }
}



// ------------------------------------------------------------ EXPORTS ------------------------------------------------------------ //

export { Vis, drawVis, updateNodes, returnClusters, clusterMode, addNodes, reset };