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

// Neovis.js options
var Vis;
var nodes;
var edges;



// ------------------------------------------------------------ FUNCTIONS ------------------------------------------------------------ //

// ------------------------------ Function-1 ------------------------------
function drawVis() {
    nodes = new vis.DataSet();
    // create an array with edges
    edges = new vis.DataSet();
    // create a network
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
    Vis = new vis.Network(container, data, options);
  }



// ------------------------------ Function-2 ------------------------------
  

// ------------------------------------------------------------ EXPORTS ------------------------------------------------------------ //

export { drawVis, Vis, nodes, edges };