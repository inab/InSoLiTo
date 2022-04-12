// Dependencies
import $ from 'jquery';
import 'jquery-ui/ui/core';
import 'jquery-ui/ui/widgets/slider.js';
import 'jquery-ui/ui/widgets/autocomplete.js';
import {NeoVis} from 'neovis.js/dist/neovis.js';
import { NEOVIS_ADVANCED_CONFIG } from 'neovis.js/dist/neovis.js'
import { objectToTitleHtml } from 'neovis.js/dist/neovis.js'

// Style 
import 'jquery-ui/themes/base/theme.css';
import 'jquery-ui/themes/base/slider.css';
import './styles/style.css';


//JSON
import OccurData from '../../DB/sliderData.json';
import ToolTopicData from '../../DB/ToolTopicAutocomplete.json';

//Images
import ToolImage from './images/tool_centered_sm.png';
import PaperImage from './images/paper_centered_sm.png';
import DatabaseImage from './images/database_centered_sm.png';
import TopicImage from './images/topic_centered_sm.png';

// Neovis.js options 
var Viz;
window.onload = function drawNeoViz() {
	var config = {
		containerId: 'Viz',
		neo4j: {
			serverUrl: 'bolt://localhost:7687',
			serverUser: 'neo4j',
			serverPassword: '1234'
		},
		visConfig: {
			layout: {
				randomSeed: 34
			},
			physics: {
				forceAtlas2Based: {
					gravitationalConstant: -200,
					//                             centralGravity: 0.005,
					springLength: 400,
					springConstant: 0.36,
					avoidOverlap: 1
				},
				maxVelocity: 30,
				solver: 'forceAtlas2Based',
				timestep: 1,
				stabilization: {
					enabled: true,
					iterations: 2000,
					updateInterval: 25,
					fit:true
				},

			},
			interaction: {
				tooltipDelay: 200,
				navigationButtons: true,
				keyboard: true
			},
			nodes: {
				shapeProperties: {
					interpolation: false    // 'true' for intensive zooming
				}
			}
		},
		labels: {
			Publication: {
				label: 'subtitle',
				group: 'community',
				[NEOVIS_ADVANCED_CONFIG]: {
					static: {
						image:  PaperImage,
						shape: 'circularImage'
						//                                 color: "#97c2fc",
					},
					function: {
						title: (props) => objectToTitleHtml(props, ['title', 'year'])
					}
				},
			},
			Tool: {
				label: 'name',
				group: 'community',
				[NEOVIS_ADVANCED_CONFIG]: {
					static: {
						image:  ToolImage,
						shape: 'circularImage'
					}
				}
			},
			Database: {
				label: 'name',
				//value: "pageRank",
				group: 'community',
				[NEOVIS_ADVANCED_CONFIG]: {
					static: {
						image: DatabaseImage,
						shape: 'circularImage'
					}
				}
			}
		},
		relationships: {
			//                     METAOCCUR: {
			//                         value: "times",
			//                         title: "year"
			//                     },
			METAOCCUR_ALL: {
				value: 'times'
			}
		},
		arrows: false,
	};
	Viz = new NeoVis(config);
	Viz.render();

}

// Barchart functions
var myCanvas = document.getElementById('myCanvas');

function drawLine(ctx, startX, startY, endX, endY, color) {
	ctx.save();
	ctx.strokeStyle = color;
	ctx.beginPath();
	ctx.moveTo(startX, startY);
	ctx.lineTo(endX, endY);
	ctx.stroke();
	ctx.restore();
}

function drawBar(ctx, upperLeftCornerX, upperLeftCornerY, width, height, color) {
	ctx.save();
	ctx.fillStyle = color;
	ctx.fillRect(upperLeftCornerX, upperLeftCornerY, width, height);
	ctx.restore();
}

var Barchart = function (options) {
	this.options = options;
	this.canvas = options.canvas;
	this.ctx = this.canvas.getContext('2d');
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
			var gridY = canvasActualHeight * (1 - gridValue / maxValue) + this.options.padding;
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
		var barSize = (canvasActualWidth) / numberOfBars;

		for (categ in this.options.data) {
			var val = this.options.data[categ];
			var barHeight = Math.round(canvasActualHeight * val / maxValue);
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
	}
}

// Barchart options
var myBarchart = new Barchart(
	{
		canvas: myCanvas,
		padding: 0,
		data: OccurData,
		colors: ['#36aaf7']
	}
);
// Initialize Barchart
myBarchart.draw();


// Function to scale the horitzontal values of the range slider
function logslider(position) {
	// position will be between 0 and 100
	var minp = 0;
	var maxp = 100;

	// The result should be between 100 an 10000000
	var minv = Math.log(parseInt(Object.keys(OccurData)[0]));
	var maxv = Math.log(parseInt(Object.keys(OccurData)[Object.keys(OccurData).length - 1]));

	// calculate adjustment factor
	var scale = (maxv - minv) / (maxp - minp);

	return Math.trunc(Math.exp(minv + scale * (position - minp)));
}

// Function to update InSoLiTo everytime the range slider changes
function updateNodes(){
	// Take name and id of all the tools and topics in the Label Menu
	// Store the values in the dictionary
	var nameNodeDict = {};
	['delete Tool','delete Topic'].forEach( className => {
		console.log(className);
		var listLegend = document.getElementsByClassName(className);
		for (var i = 0; i < listLegend.length; i++) {
			console.log(listLegend[i].textContent);
			var nameNode = listLegend[i].textContent;
			var idNode = listLegend[i].value;
			var typeNode = className.substring(7,className.length)
			nameNodeDict[nameNode] =[idNode, typeNode];
		}
	});
	// Clear the webpage
	reset();
	// Readd the nodes from the Label Menu
	for(const [nameNode, listNode] of Object.entries(nameNodeDict)) {
		// Take the Min and Max cooccurrence value between the relationships
		var cMin = $('#amount').val().substr(0, $('#amount').val().indexOf('-') - 1);
		var cMax = $('#amount').val().substr($('#amount').val().indexOf('-') + 2, $('#amount').val().length);
		console.log(listNode, listNode[0], listNode[1]);
		addNodes(nameNode, listNode[0], cMin, cMax, listNode[1]);

	};
}

// Slider range function
$(function () {
	$('#slider-range').slider({
		range: true,
		min: 0,
		max: 100,
		values: [0, 100],
		slide: function (event, ui) {
			$('#amount').val(logslider(ui.values[0]) + ' - ' + logslider(ui.values[1]));
		},
		// When slider range changes, update the nodes
		change: function(){
			updateNodes();
		}
	});
	$('#amount').val(logslider($('#slider-range').slider('values', 0)) +
	' - ' + logslider($('#slider-range').slider('values', 1)));
});

// Autcomplete Function for the Search box
$(function () {
	$('#tooltopic_autocomplete').autocomplete({
		source: ToolTopicData,
		minLength: 1,
		select: function (event, ui) {
			// Select Name and Id of tool
			var name = ui.item.value;
			var idNode = ui.item.idNodes;
			var idEdge = ui.item.idEdges;
			var typeNode = ui.item.labelnode;
			if (Array.isArray(typeNode)){
				var typeNode = typeNode[0];
			}
			// Take the Min and Max cooccurrence value between the relationships
			var cMin = $('#amount').val().substr(0, $('#amount').val().indexOf('-') - 1);
			var cMax = $('#amount').val().substr($('#amount').val().indexOf('-') + 2, $('#amount').val().length);
			//Add Nodes from the autocomplete
			addNodes(name, idNode, idEdge, cMin, cMax, typeNode);
			$(this).val('');
			return false;

		},
		open: function () {
			$('.ui-autocomplete').css('z-index', 1000);
		}
	})// Output of the textbox
		.autocomplete('instance')._renderItem = function (ul, item) {
			if (item.labelnode[0] === 'Tool'){
				return $('<li class="no-bullets"><div class="boxAutocomplete"><img src="' + ToolImage +'"><span class="TextAutocomplete">' + item.value + '</span></div></li>').appendTo(ul);
			}
			else if (item.labelnode[0] === 'Database'){
				return $('<li class="no-bullets"><div class="boxAutocomplete"><img src="' + DatabaseImage +'"><span class="TextAutocomplete">' + item.value + '</span></div></li>').appendTo(ul);

			} else {
				return $('<li class="no-bullets"><div class="boxAutocomplete"><img src="' + TopicImage + '"><span class="TextAutocomplete">' + item.value + '</span></div></li>').appendTo(ul);

			}
		}
});

// Empty the legend
function removeLegend(){
	console.log('removing legend');
	const list = document.querySelector('#legend ul');
	list.innerHTML = '';

}

// Function that retrieves the id and size of the communities from the graph
function returnClusters() {
	var net = Viz.network.body;
	var allNodes = net.nodeIndices;

	var dictClusters = {};
	
	// For each node found in the graph
	allNodes.forEach((node) => {
		// Store their id and color
		var commId = net.nodes[node].options.raw.properties.community;
		var colorId = net.nodes[node].options.color.background;
		// Count how many times the same community is found
		if (dictClusters.hasOwnProperty(commId)){
			dictClusters[commId].count += 1;
		}
		// If the node has an unknow community, initialize it
		else{
			dictClusters[commId] = {count : 1, cTopic:{}, color: colorId};
		}
		// Store and count the EDAM terms of each tool inside each community 
		if (net.nodes[node].options.raw.properties.hasOwnProperty('topiclabel')){
			var listTopics = net.nodes[node].options.raw.properties.topiclabel;
			listTopics.forEach((topic) =>{
				if(dictClusters[commId].cTopic.hasOwnProperty(topic)){
					dictClusters[commId].cTopic[topic] += 1;
				} 
				else {
					dictClusters[commId].cTopic[topic] = 1;
				}
			});
		}
		
	});
	return dictClusters;
}

// Insert the legend in the HTML
function addLegend() {
	var optionRadio = document.querySelector('input[name="cluster_mode"]:checked');
	const list = document.querySelector('#legend ul');
	console.log('Addlegend');
	// If normal colors
	if(optionRadio.value==='Normal'){
		// Insert the different type of nodes in the legend (Publication, Tool, Dataset)
		console.log('normal');
		list.innerHTML = '<div id="legendnormal"><img style="background-color: #add8e6;" src=' + ToolImage + ' ><span> Tools </span></div>';
		list.innerHTML +='<div id="legendnormal"><img style="background-color: #FB7E81;" src=' + PaperImage + '><span> Articles </span></div>';
		list.innerHTML +='<div id="legendnormal"><img style="background-color: #b2e6ad;" src=' + DatabaseImage + '><span> Databases </span></div>';

	}
	// If Cluster mode, you take the colors from each community
	// If there are less than 10 nodes, don't write the community in the legend
	else{
		list.innerHTML = '';
		console.log('cluster');
		// Retrieve community ids and their size
		var dictClusters = returnClusters();
		
		for(const [, cvalue] of Object.entries(dictClusters)) {
			// There must be more than 9 nodes to show the community in the legend
			if(cvalue.count >9){
				let maxKey = [];
				let maxValue = 0;
				for(const [tkey, tvalue] of Object.entries(cvalue.cTopic)) {
					// store the EDAM term with the highest population possible in each community
					if(tvalue > maxValue) {
						maxKey = [tkey];
						maxValue = tvalue;
					}
					// If two or more edam terms have the same population
					// Insert them in the same array
					else if(tvalue === maxValue){
						maxKey.push(tkey);
					}
				}
				console.log(maxKey, maxValue, cvalue.color);
				// Append all the communities in the legend with its color
				list.innerHTML += '<div><div id="circle" style="background-color:' + cvalue.color + ';"></div><span>' + maxKey.join(' / ') + '</span></div>';
			}
		}
	}
}

// Function that store the community color of the nodes
// And store the color representing the type of node that they are (Publication, Tool, Database)
function storeClusterColor(){
	setTimeout(function() {
		var net = Viz.network.body;
		var allNodes = net.nodeIndices;
		// For each node
		allNodes.forEach((node) => {
			if (net.nodes[node].options.hasOwnProperty('colorcluster')){
				return true;
			}
			// Create a dictionary for storing the color of the Cluster mode
			var objCluster ={colorcluster :{background:null, border:null, highlight:{background: null, border:null}, hover:{background: null, border:null}}};
			// Store the color of the community
			objCluster.colorcluster.background = net.nodes[node].options.color.background;
			objCluster.colorcluster.border = net.nodes[node].options.color.border
			objCluster.colorcluster.highlight.background = net.nodes[node].options.color.highlight.background
			objCluster.colorcluster.highlight.border = net.nodes[node].options.color.highlight.border
			objCluster.colorcluster.hover.background = net.nodes[node].options.color.hover.background
			objCluster.colorcluster.hover.border = net.nodes[node].options.color.hover.border
			// Insert the colors of the different type of nodes in the dictionary
			var objNormal = {colornormal :{background:null, border:null, highlight:{background: null, border:null}, hover:{background: null, border:null}}};
			if (net.nodes[node].options.raw.labels[0]==='Tool'){
				objNormal.colornormal.background='#add8e6'
				objNormal.colornormal.border='#6bc5e3'
				objNormal.colornormal.highlight.background='#add8e6'
				objNormal.colornormal.highlight.border='#6bc5e3'
				objNormal.colornormal.hover.background='#add8e6'
				objNormal.colornormal.hover.border='#6bc5e3'
			}
			else if (net.nodes[node].options.raw.labels[0]==='Database'){
				objNormal.colornormal.background='#b2e6ad'
				objNormal.colornormal.border='#4ed442'
				objNormal.colornormal.highlight.background='#b2e6ad'
				objNormal.colornormal.highlight.border='#4ed442'
				objNormal.colornormal.hover.background='#b2e6ad'
				objNormal.colornormal.hover.border='#4ed442'
			}
			else{
				objNormal.colornormal.background='#FB7E81'
				objNormal.colornormal.border='#FA0A10'
				objNormal.colornormal.highlight.background='#FB7E81'
				objNormal.colornormal.highlight.border='#FA0A10'
				objNormal.colornormal.hover.background='#FB7E81'
				objNormal.colornormal.hover.border='#FA0A10'
			}
			// Update the nodes with the color information
			net.nodes[node].options = Object.assign(net.nodes[node].options, objCluster)
			net.nodes[node].options = Object.assign(net.nodes[node].options, objNormal)
		});
	});

}

// Function that changes the color of the nodes - Cluster/Normal mode
function clusterMode(){
	// Check the color mode
	var optionRadio = document.querySelector('input[name="cluster_mode"]:checked');
	console.log(optionRadio.value);
	// List where the new colors of the nodes will be stored
	var listChanges = [];
	// Variables to shorten paths
	var net = Viz.network.body;
	var allNodes = net.nodeIndices;
	// For each node displayed
	allNodes.forEach((node) => {
		// Path for Cluster Mode
		if(optionRadio.value === 'Cluster'){
			var colorNodePath = net.nodes[node].options.colorcluster;
		}
		// Path for Normal Mode
		else{
			var colorNodePath = net.nodes[node].options.colornormal;
		}
		// Assign new color to node
		var changeNode = {
			id:node,
			color: {
				background: colorNodePath.background,
				border: colorNodePath.border,
				highlight: {
					border: colorNodePath.highlight.border,
					background: colorNodePath.highlight.background
				},
				hover : {
					border: colorNodePath.hover.border,
					background: colorNodePath.hover.background
				}
			}
		};
		listChanges.push(changeNode);
	});
	// Update nodes
	Viz.nodes.update(listChanges);

} 

$('input[type=radio][name=cluster_mode]').change(function(){
	// Change color of the nodes
	clusterMode();
	// Update legend
	addLegend();
});

// function addLabelMenu(name, idNode, idEdge) {
// 	const list = document.querySelector('#tools-list ul');

// 	// create elements
// 	const value = name
// 	const li = document.createElement('li');
// 	const ToolName = document.createElement('span');
// 	//   const deleteBtn = document.createElement('span');

// 	// add text content
// 	ToolName.textContent = value;
// 	//   deleteBtn.textContent = 'delete';
// 	// add classes
// 	ToolName.classList.add('delete', 'Tool');
// 	ToolName.value = idNode;

// 	// append to DOM
// 	li.appendChild(ToolName);
// 	//   li.appendChild(deleteBtn);
// 	list.appendChild(li);
// 	//list.insertBefore(li, list.querySelector('li:first-child'));

// 	// delete books
// 	list.addEventListener('click', (e) => {
// 		if (e.target.className === 'delete Tool') {
// 			console.log('Removing Tool');
// 			const li = e.target.parentElement;
// 			li.parentNode.removeChild(li);
// 			var IdTool = e.target.value;
// 			console.log(IdTool);

// 			Viz.network.unselectAll();
// 			var ConnectedNodes = Viz.network.getConnectedNodes(IdTool);

// 			var UnconnectedNodes = [];
// 			ConnectedNodes.forEach((node) => {
// 				if (Viz.network.getConnectedEdges(node).length === 1) {
// 					UnconnectedNodes.push(node);
// 				};
// 			});
// 			Viz.network.selectNodes([e.target.value].concat(UnconnectedNodes));
// 			Viz.network.deleteSelected();
// 			addLegend();
// 		};
// 	});
// }

// Initialize Menu
function algo(cMin,cMax){
	// When node selected, activate the menu
	Viz.network.on('selectNode', (e1) => {
		console.log('selecting');
		console.log(e1);
		menu(e1, cMin, cMax);
	});
	// When nodes are not selected, delete the menu
	Viz.network.on('deselectNode', () => {
		console.log('deselect');
		var contextMenu = document.getElementById('context-menu');
		contextMenu.innerHTML = '';
	});
}

// Remove all the Tools and Topics from the Label Menu
function removeAllToolsMenu() {
	console.log('removeAllToolsMenu');
	const list = document.querySelector('#tools-list ul');
	list.innerHTML = '';
}

// Run a Cypher query that will be displayed in the web 
async function addNodesGraph(NameNode, cMin, cMax, typeNode) {
	// Cypher query
	var cypherQuery = '';
	if (typeNode==='Tool'){
		cypherQuery = 'MATCH (i)-[o:METAOCCUR_ALL]-(p) where i.name="' + NameNode + '" and o.times>' + cMin + ' and o.times<' + cMax + ' return i,o,p order by o.times';
	}
	else{
		cypherQuery = 'match (n)-[:TOPIC]->(k:Keyword)-[:SUBCLASS*]->(k2:Keyword) where k2.label="' + NameNode + '" or k.label="' + NameNode + '" with distinct n with collect(n) as nt unwind nt as nt1 unwind nt as nt2 match (nt1)-[m:METAOCCUR_ALL]-(nt2) where m.times>=' + cMin + ' and m.times<= ' + cMax + ' return nt1,m,nt2';
	}
	// Run query
	Viz.updateWithCypher(cypherQuery);
	console.log(cypherQuery);
	// Display loading screen until the query is fully displayed
	const list = document.querySelector('#loading');
	const Loadingtext = document.createElement('span');
	Loadingtext.textContent = 'Loading...';
	Loadingtext.classList.add('loadingbar');
	list.appendChild(Loadingtext);
	// If no results found, wait and put an alert
	await new Promise(r => setTimeout(r, 5000));
	console.log(Viz.nodes.length);
	if (Viz.nodes.length === 0) {
		alert('No results found. Try again!');
	}
	// Initialize Right-click Menu
	algo(cMin, cMax);
	// Wait until the colors of the nodes are stored and fully displayed in the web
	await new Promise(() => {
		storeClusterColor();
		waitAddTool();
	});
}
// Function to add nodes in the web and insert their names in the Label Menu
function addNodes(nameNode, idNode, idEdge, cMin, cMax, nodeType) {

	var list = document.getElementsByClassName('delete');
	var isInMenu = false;
	// If name already in the label menu
	Array.prototype.forEach.call(list, function (tool) {
		console.log(tool);

		if (tool.textContent === nameNode) {
			console.log(nameNode);
			isInMenu = true;
		}
	});
	// If name of tool/topic not in menu
	if (isInMenu === false) {
		addNodesGraph(nameNode, cMin, cMax, nodeType)
		addLabelMenu(nameNode, idNode, idEdge, nodeType);

	}
}

function centerNode(name, idNode, idEdge, cMin, cMax) {
	reset();
	addNodes(name, idNode, idEdge, cMin, cMax, 'Tool');
}

function addLabelMenu(NameTopic, idNode, idEdge, nodeType) {
	const list = document.querySelector('#tools-list ul');

	// create elements
	const value = NameTopic
	const li = document.createElement('li');
	const ToolName = document.createElement('span');

	// add text content
	ToolName.textContent = value;
	// add classes
	ToolName.classList.add('delete', nodeType);
	ToolName.value = [idNode, idEdge];

	// append to DOM
	li.appendChild(ToolName);
	list.appendChild(li);

	// delete Labels
	list.addEventListener('click', (e) => {
			const li = e.target.parentElement;
			li.parentNode.removeChild(li);
			var IdTool = e.target.value[0];
			var IdToolEdge = e.target.value[1];
			console.log(IdTool);
			console.log(IdToolEdge);
			if (e.target.className === 'delete Topic') {
				console.log('removing topic');
				IdToolEdge.forEach((edge) =>{
					if (Viz.edges.get(edge)!== null){
						Viz.network.selectEdges([edge]);
						Viz.network.deleteSelected();
					}
				});
				// IdTool.forEach((node)=> {
				// 	if (Viz.nodes.get(node)!== null){
				// 		var nodesInsideTopic = true;
				// 		var ConnectedNodes = Viz.network.getConnectedNodes(node);
				// 		console.log(node, ConnectedNodes)
				// 		ConnectedNodes.forEach((nodeTopic) =>{
				// 			if (!(IdTool.includes(nodeTopic))){
				// 				console.log(nodeTopic);
				// 				nodesInsideTopic = false;
				// 			}
				// 		})
				// 		if (nodesInsideTopic){
				// 			Viz.network.selectNodes([node]);
				// 			Viz.network.deleteSelected();
				// 		}
				// 	}
				// });
			}
			else{
				console.log('removing tool');
				
				var ConnectedNodes = Viz.network.getConnectedNodes(IdTool);

				var UnconnectedNodes = [];
				ConnectedNodes.forEach((node) => {
					if (Viz.network.getConnectedEdges(node).length === 1) {
						UnconnectedNodes.push(node);
					};
				});
				Viz.network.selectNodes([IdTool].concat(UnconnectedNodes));
				Viz.network.deleteSelected();
			}
			var graphNodes = Viz.nodes.getIds();
			graphNodes.forEach((node) =>{
				if (Viz.network.getConnectedNodes(node).length === 0){
					Viz.network.selectNodes([node]);
					Viz.network.deleteSelected();
				}

			})

			addLegend();
	});
}


function menu(e1, cMin, cMax) {
	if (e1.nodes.length === 1) {
		var nodeId = e1.nodes[0];
		var idEdge = []; 
		if (Viz.network.body.nodes[nodeId].options.raw.labels[0] === 'Publication') {
			return;
		}
		
		console.log(nodeId);
		console.log(Viz.network.body.nodes[nodeId]);

		// Display menu
		const contextMenu = document.getElementById('context-menu');
		contextMenu.innerHTML = '<div class="topicmenu" id="topic"></div><div class="item" id = "webpage"></div><div class="item" id="center"></div><div class="item" id="expand"></div>'
		const scope = document.querySelector('body');

		var name = Viz.network.body.nodes[nodeId].options.raw.properties.name;
		console.log(name);

		var label = Viz.network.body.nodes[nodeId].options.raw.properties.label;
		console.log(label);


		if ('topiclabel' in Viz.network.body.nodes[nodeId].options.raw.properties) {
			var topiclabel = Viz.network.body.nodes[nodeId].options.raw.properties.topiclabel;
			console.log(topiclabel.length);

			var topicedam = Viz.network.body.nodes[nodeId].options.raw.properties.topicedam;
			console.log(topicedam);

			document.getElementById('topic').innerHTML = '';
			for (var i = 0; i < topiclabel.length; i++) {
				var buttonTopic = document.createElement('button');
				buttonTopic.className= 'TopicButton';
				buttonTopic.innerText = topiclabel[i];
				buttonTopic.value = topiclabel[i];
				console.log(buttonTopic.innerText)
				document.getElementById('topic').appendChild(buttonTopic);
			}
		}
		var buttonTopic=document.getElementsByClassName('TopicButton');
		for (var i = 0; i < buttonTopic.length; i++){
			buttonTopic[i].addEventListener('click', function (buttonTopic) {
				console.log(buttonTopic);
				addNodes(buttonTopic.srcElement.value, cMin, cMax, 'Topic');
			});
		}

		document.getElementById('webpage').innerHTML = '<button onclick="window.open(&#34;https://openebench.bsc.es/tool/' + label + '&#34; , &#34;_blank&#34; )">Webpage</button>';

		var buttonCenter = document.createElement('button');
		buttonCenter.innerText = 'Center';
		buttonCenter.addEventListener('click', function() {
			centerNode(name, nodeId, idEdge, cMin, cMax);
		});
		document.getElementById('center').appendChild(buttonCenter);

		var buttonExpand = document.createElement('button');
		buttonExpand.innerText = 'Expand';
		buttonExpand.addEventListener('click', function() {
			addNodes(name, nodeId, idEdge, cMin, cMax, 'Tool');
		});
		document.getElementById('expand').appendChild(buttonExpand);

		const normalizePozition = (mouseX, mouseY) => {
			// ? compute what is the mouse position relative to the container element (scope)
			let {
				left: scopeOffsetX,
				top: scopeOffsetY,
			} = scope.getBoundingClientRect();

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

		scope.addEventListener('contextmenu', (event) => {
			event.preventDefault();


			const { clientX: mouseX, clientY: mouseY } = event;

			const { normalizedX, normalizedY } = normalizePozition(mouseX, mouseY);

			contextMenu.classList.remove('visible');

			contextMenu.style.top = `${normalizedY}px`;
			contextMenu.style.left = `${normalizedX}px`;




			setTimeout(() => {
				contextMenu.classList.add('visible');
			});
		});

		scope.addEventListener('click', (e) => {
			// ? close the menu if the user clicks outside of it
			if (e.target.offsetParent !== contextMenu) {
				contextMenu.classList.remove('visible');
			}
		});
	}
}



function addLoadingTool (){ 
	setTimeout(function () {
		clusterMode();
	})
	var loadingid = document.querySelector('.loadingbar');
	console.log(loadingid);
	Viz.stabilize();


	// loadingid.parentElement.removeChild(loadingid);
	Viz.network.off('afterDrawing', addLoadingTool);
	// Viz.network.fit();
	Viz.stabilize(100);
	loadingid.parentNode.removeChild(loadingid);

};

function waitAddTool(){
	setTimeout(function(){
		console.log('add stabilize')
		Viz.network.stabilize(100);
		Viz.network.on('afterDrawing', addLoadingTool);

	})
}


function reset(){
	console.log('reset');
	Viz.reload();
	removeAllToolsMenu();
	removeLegend();
}


const res = document.getElementById('reset');

// Reset All Neo4j
res.addEventListener('click', () => {
	reset();
});



const sta = document.getElementById('stabilize');

// Stabilize the network
sta.addEventListener('click', () => {
	Viz.stabilize();

	console.log(Viz.network.body.nodes[124498]);

});
