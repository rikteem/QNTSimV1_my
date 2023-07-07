var currentTab;
var pages = 6;
var nodes = [];

$(document).ready(function () {
	currentTab = 0; // Current tab is set to be the first tab (0)
	showTab(currentTab); // Display the current tab
	fixButtons(currentTab);
	fixStepIndicator(currentTab);
	$(".addRow").click(function (e) { 
		e.preventDefault();
		addRow($(this.parentElement).children("table")[0].id);
	});
});

function convertFormToJSON(form) {
	const array = $(form).serializeArray(); // Encodes the set of form elements as an array of names and values.
	const json = {};
	$.each(array, function () {
	  json[this.name] = this.value || "";
	});
	return json;
}

function deleteRow(row) {
	$(row.parentElement.parentElement).remove();
}

function addRow(tableID) {
	// console.log(`Adding row to table: ${tableID}`);
	// console.log(nodes);
	// var noOfCols = $(`#${tableID}`).find("th").length;
	var HTML = `<tr>`;
	var nodeOptsHTML = '';
	nodes.forEach(node => {
		nodeOptsHTML += `<option value="${node}">${node}</option>`;
	});
	
	switch(tableID){
		case "nodes":
			HTML += `<td><input type="text" name="nodeName"></td>
					<td><select name="nodeType"><option value="service" default>Service</option><option value="end">End</option></select></td>
					<td><input type="text" name="nodeNoMemories" value="500"></td>
					<td><input type="text" name="nodeMemoFreq" value="2e3"></td>
					<td><input type="text" name="nodeMemoExpiry" value="0"></td>
					<td><input type="text" name="nodeMemoEfficiency" value="1"></td>
					<td><input type="text" name="nodeMemoFidelity" value="0.93"></td>`;
			break;
		case "qc" :
			HTML += `<td><select name="qcNode1">${nodeOptsHTML}</select></td>
					<td><select name="qcNode2">${nodeOptsHTML}</select></td>
					<td><input type="text" name="qcAttenuation" value="1e-5"></td>
					<td><input type="text" name="qcDistance" value="70"></td>`;
				break;
		case "vc" :
			HTML += `<td><select name="vcNode1">${nodeOptsHTML}</select></td>
					<td><select name="vcNode2">${nodeOptsHTML}</select></td>
					<td><input type="text" name="vcDemandSize" value="50"></td>`
				break;
	}

	//HTML += `<td><button type="button" class="deleteRow" onclick="deleteRow(this)">Delete Node</button></td></tr>`;
	HTML += `<td><a class="banner-button btn rounded-pill btn-outline-primary btn-md px-4 deleteRow" role="button" onclick="deleteRow(this)">Delete</a></td></tr>`;

	$(`#${tableID}`).append(HTML);
}

function setSenderReceiver() {
	$(".appnode").empty();

	var nodeOpts = ``;
	nodes.forEach(node => {
		nodeOpts += `<option name="${node}" value="${node}">${node}</option>`;
	});

	$(".appnode").append(nodeOpts);
}

function fetchTopology(){
	console.log("Fetching topology");

	var nodeArray = [];
	$('#nodes > tbody  > tr').each(function() {
		nodeArray.push({
			"Name": $(this).find('[name=nodeName]')[0].value,
			"Type": $(this).find('[name=nodeType]')[0].value,
			"noOfMemory": Number($(this).find('[name=nodeNoMemories]')[0].value),
			"memory": {
				"frequency": Number($(this).find('[name=nodeMemoFreq]')[0].value),
				"expiry": Number($(this).find('[name=nodeMemoFreq]')[0].value),
				"efficiency": Number($(this).find('[name=nodeMemoExpiry]')[0].value),
				"fidelity": Number($(this).find('[name=nodeMemoFidelity]')[0].value),
			},
		});
	});
	var qc = [];
	$('#qc > tbody  > tr').each(function() {
		qc.push({
			"Nodes": [$(this).find('[name=qcNode1]')[0].value, $(this).find('[name=qcNode2]')[0].value],
			"Attenuation": Number($(this).find('[name=qcAttenuation]')[0].value),
			"Distance": Number($(this).find('[name=qcDistance]')[0].value),
		});
	});
	var cc = [];
	$('#cc tbody input').each(function() {
		var nodes = $(this).data('nodes');
		if(nodes){
			cc.push({
				"Nodes": nodes,
				"Delay": Number($(this).val()),
				"Distance": 1e3,
			});
		}
	});
	var topology = {
		"nodes": nodeArray,
		"quantum_connections": qc,
		"classical_connections": cc,
	};
	console.log(JSON.stringify(topology));
	return topology;
}

function fetchApp(){
	return $("#app").val();
}

function fetchAppSettings(){
	const formData = convertFormToJSON($("#appConf form"));
	return formData;
}

function fetchTopologyGraph(){
	console.log("Fetching topology graph");
	var topology = fetchTopology();
	console.log(`Visualising Topology : ${JSON.stringify(topology)}`);
	$.ajax({
		type: "POST",
		url: "graph",
		data: {
			"topology": JSON.stringify(topology),
		},
		success: function (response) {
			console.log(response)
			$("#topoGraph").html(response);
		}
	});
}

function createCCTable() {
	$(`#cc`).empty();
	console.log("Create Classical Connections Table");
	var HTML = `<thead><th></th>`;
	nodes.forEach(node => {
		HTML += `<th>${node}</th>`;
	});
	HTML += `</thead><tbody>`;
	nodes.forEach(node => {
		HTML += `<tr><td>${node}</td>`;
		nodes.forEach(node2 => {
			if(node == node2){
				HTML += `<td><input type="text" name="ccDelay" value="0" data-nodes=["${node}","${node2}"] disabled></td>`;
			} else {
				HTML += `<td><input type="text" name="ccDelay" value="1e9" data-nodes=["${node}","${node2}"]></td>`;
			}
		});
		HTML += `</tr></tbody>`;
	});
	$(`#cc`).html(HTML);
}

function getResults(){
	var appConf = {
		"application": fetchApp(),
		"topology": JSON.stringify(fetchTopology()),
		"appSettings": JSON.stringify(fetchAppSettings())
	}
	console.log(appConf);
	$.ajax({
		type: "POST",
		url: "run",
		data: appConf,
		success: function (response) {
			$("#results").html(response);
		}
	});
}

function showTab(n) {
	// console.log(`Showing tab: ${n+1}`);
	$(`div.tab:nth-child(${n+1})`).show();
	
	switch(n) {
		case 0:
			
			break;
		case 1:
			nodes = $(`#nodes input[name=nodeName]`).map(function() {
				// console.log($(this).val());
				return $(this).val();
			}).get();
			break;
		case 2:
			createCCTable();
			break;
		case 3:
			fetchTopologyGraph();
			break;
		case 4:
			setSenderReceiver();
			break;
		case 5:
			getResults();
			break;
	}
}

function validate(currentTab){
	return true;

	// TODO: Check if empty
	// var x, y, i, valid = true;
	// x = document.getElementsByClassName("tab");
	// y = x[currentTab].getElementsByTagName("input");
	// // A loop that checks every input field in the current tab:
	// for (i = 0; i < y.length; i++) {
	//   // If a field is empty...
	//   if (y[i].value == "") {
	// 	// add an "invalid" class to the field:
	// 	y[i].className += " invalid";
	// 	// and set the current valid status to false:
	// 	valid = false;
	//   }
	// }
	// // If the valid status is true, mark the step as finished and valid:
	// if (valid) {
	//   document.getElementsByClassName("step")[currentTab].className += " finish";
	// }
	// return valid; // return the valid status

	// switch(currentTab) {
	// 	case 0:
	// 		var tempNodes = [];
	// 		$("#nodes input[name='nodeName']").each(function (index, element) { 
	// 			tempNodes.push($(element).val());
	// 		});
	// 		//Nodes cannot be null
	// 		nodes = tempNodes;
	// 		break;
	// 	case 1:
	// 		break;
	// 	case 2:
	// 		break;
	// 	case 3:
	// 		break;
	// 	case 4:
	// 		break;
	// 	case 5:
	// 		break;
	// 	case 6:
	// 		break;
	// }
}

function nextPrev(n) {
	var validation = validate(currentTab);
	// Validate if we can proceed to next tab
	if(validation === true){
		// Hide previous tab and show next one
		$(`div.tab:nth-child(${currentTab+1})`).hide();
		currentTab = currentTab + n;
		// console.log("New Tab: " + currentTab);
		showTab(currentTab);

		// ... and run a function that displays the correct step indicator:
		fixStepIndicator(currentTab)
		fixButtons(currentTab);	
	}else{
		// Display error message if validations fail
		$("#error").text = validation;
		return ;
	}
}
 
function fixStepIndicator(n) {
	// console.log(`Fixing Step Indicator: ${n}`);

	  // This function removes the "active" class of all steps...
	  var i, x = document.getElementsByClassName("step");
	//   console.log(x);
	//   console.log(n);
	for (i = 0; i < x.length; i++) {
	  x[i].className = x[i].className.replace(" active", "");
	}
	//... and adds the "active" class to the current step:
	x[n].className += " active";
}

function fixButtons(n){
	// console.log(`Fixing Buttons ${n}`);
	//Set the Buttons
	if (n == 0) {
		$("#prevBtn").hide();
	} else {
		$("#prevBtn").show();
	}
	if (n == (pages - 1)) {
		$("#nextBtn").hide();
	} else {
		$("#nextBtn").show();
	}
}