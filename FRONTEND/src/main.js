// Dependencies
import $ from "jquery";
import "jquery-ui/ui/core";
import "jquery-ui/ui/widgets/slider.js";
import "jquery-ui/ui/widgets/autocomplete.js";

// Style
import "jquery-ui/themes/base/theme.css";
import "jquery-ui/themes/base/slider.css";
import "vis-network/dist/dist/vis-network.min.css";
import "./styles/extras.scss";
import "./styles/style.css";

import * as bootstrap from 'bootstrap'
import sampleConfig from "./config.json";

import OccurData from "../../DB/RelationshipSliderData.json";
import YearData from "../../DB/YearSliderData.json";
import ToolTopicData from "../../DB/ToolTopicAutocomplete.json";

// Images
import ToolImage from "./images/tool_centered_sm.png";
import DatabaseImage from "./images/database_centered_sm.png";
import TopicImage from "./images/topic_centered_sm.png";
import logoInSoLiTo from "./images/logo_InSoLiTo.png";

// Modules
import { actionSidebar, Barchart, sliderRangeFunction, addLegend, initAutocomplete, removeAllTopicsMenu } from "./modules.js/navBar";
import { Vis, drawVis, updateNodes, clusterMode, addNodes, reset } from "./modules.js/graph";

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
    if ($("#yearColumn").hasClass("disp-block")) {
      $("#yearColumn").removeClass("disp-block");
    }
    $("#yearColumn").addClass("hidden");
  } else {
    if ($("#yearColumn").hasClass("hidden")) {
      $("#yearColumn").removeClass("hidden");
    }
    $("#yearColumn").addClass("disp-block");
  }
});

$("#reset").on("click", function () {
  removeAllTopicsMenu();
  reset();
});

$("#stabilize").on("click", () => {
  Vis.stopSimulation();
});

