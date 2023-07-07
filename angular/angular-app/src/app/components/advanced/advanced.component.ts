import { AfterViewInit, Component, ElementRef, HostListener, OnDestroy, OnInit, ViewChild, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormControl, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { Subscription, map } from 'rxjs';
import { environment } from 'src/environments/environment';

import { ConfirmationService, MessageService } from 'primeng/api';

import { ApiServiceService } from 'src/services/api-service.service';
import { ConditionsService } from 'src/services/conditions.service';
import { DiagramStorageService } from 'src/services/diagram-storage.service';
import { HoldingDataService } from 'src/services/holding-data.service';

import * as go from 'gojs';
import { DiagramBuilderService } from 'src/services/diagram-builder.service';

@Component({
  selector: 'app-advanced',
  templateUrl: './advanced.component.html',
  styleUrls: ['./advanced.component.less'],
  providers: [MessageService, ConfirmationService],
  encapsulation: ViewEncapsulation.Emulated
})
export class AdvancedComponent implements OnInit, AfterViewInit, OnDestroy {
  app: any
  adornedpart: any
  routeFrom: string
  linkConnection = {
    key: -1,
    from: -1,
    to: -1,
    distance: 70,
    attenuation: 0.0001
  }
  @ViewChild('diagramContainer') private diagramRef: ElementRef;
  private addButtonAdornment: go.Adornment;
  nodeTypeSelect: boolean = false
  private subscription: Subscription;
  nodesSelection = {
    sender: '',
    receiver: '',
    endNode1: '',
    endNode2: '',
    endNode3: '',
    middleNode: '',
    attack: 'none',
    numDecoy: 4,
    numCheckBits: 4,
    errorThreshold: 0.5,
    message: '001100',
    senderId: 1010,
    receiverId: 1011,
    bellType: "10",
    channel: 1,
    switchProb: 0
  }
  detectorProps = {
    efficiency: 1,
    countRate: 25000000,
    timeResolution: 150,
    powerLoss: 0,
    swapSuccess: 0.99
  }
  lightSourceProps = {
    frequency: 8000000,
    wavelength: 1550,
    bandwidth: 50,
    meanPhotonNum: 0.5,
    phaseError: 0
  }
  simulator = {
    value: 'version1',
    options: [{
      header: 'Version 1', value: 'version1'
    },
    {
      header: 'Version 2', value: 'version2'
    }]
  };
  isLinkParameters: boolean = false
  linksProps = {
    distance: 70,
    attenuation: 0.0001,
    keySelected: 1
  }
  linkData: any = {}
  link_array: any = []
  app_id: any
  nodesData: any = {}
  serviceNodes: any[] = []
  endNodes: any[] = []
  step: any
  cc: any = []
  topology: any
  appSettings: any
  debug = {
    loggingLevel: {
      name: 'INFO', value: 'info'
    },
    modules: []
  }
  debugOptions = {
    moduleOptions: [],
    loggingLevelOptions: []
  }
  spinner: boolean = false
  e2e = {
    targetFidelity: 0.5,
    size: 6
  }
  nodes: any = []
  attackOptions = ['DoS', "EM", "IR", "none"]
  bellTypeOptions = ["00", "01", "10", "11"];
  channelOptions = [1, 2, 3]
  public selectedLink: any
  public myDiagram: any
  links: any = [];
  application: any;
  activeIndex: number = 0;
  appSettingsForm
  app_data: { 1: string; 2: string; 3: string; 4: string; 5: string; 6: string; 7: string; 8: string; 9: string; 10: string; };
  constructor(private fb: FormBuilder,
    private con: ConditionsService,
    private apiService: ApiServiceService,
    private holdingData: HoldingDataService,
    private _route: Router,
    private diagramStorage: DiagramStorageService,
    private diagramBuilder: DiagramBuilderService) {
  }
  ngOnDestroy(): void {
    this.diagramStorage.setAppSettingsFormDataAdvanced({ app_id: this.app_id, nodesSelection: this.nodesSelection, appSettingsForm: this.appSettingsForm, e2e: this.e2e, activeIndex: this.activeIndex, detectorProps: this.detectorProps, lightSourceProps: this.lightSourceProps });
    this.subscription.unsubscribe()
  }
  @HostListener('window:resize', ['$event'])
  onResize(event: any) {
    this.step = 0;
  }
  ngAfterViewInit(): void {
    this.initDiagram();
    this.updateNodes();
    const appSettingsBackup = this.diagramStorage.getAppSettingsFormDataAdvanced()
    if (appSettingsBackup) {
      this.e2e = appSettingsBackup.e2e
      this.nodesSelection = appSettingsBackup.nodesSelection
      this.activeIndex = appSettingsBackup.activeIndex,
        this.detectorProps = appSettingsBackup.detectorProps
      this.lightSourceProps = appSettingsBackup.lightSourceProps
    }
    // this.appSettingsForm = appSettingsBackup.appSettingForm
  }

  allowBitsInput($event: any): void {
    if ($event.key.match(/[0-1]*/)['0']) { }
    else {
      $event.preventDefault();
    }
  }
  selectNodeType(adornedpart: any) {
    this.nodeTypeSelect = true;
    this.adornedpart = adornedpart
  }
  updateNodes() {
    var nodesArray = this.myDiagram.model.nodeDataArray
    this.serviceNodes = [];
    this.endNodes = [];
    this.nodes = [];
    this.nodesData = {}
    for (let i = 0; i < nodesArray.length; i++) {
      const nodereq = {
        "Name": nodesArray[i].name,
        "Type": nodesArray[i].properties[0].propValue.toLowerCase(),
        "noOfMemory": Number(nodesArray[i].properties[1].propValue),
        "memory": {
          'frequency': Number(nodesArray[i].memory[0].propValue),
          'expiry': Number(nodesArray[i].memory[1].propValue),
          'efficiency': Number(nodesArray[i].memory[2].propValue),
          'fidelity': Number(nodesArray[i].memory[3].propValue),

        },
        "swap_success_rate": 0.99,
        "swap_degradation": 1,
        "lightSource": {
          "frequency": this.lightSourceProps.frequency,
          "wavelength": this.lightSourceProps.wavelength,
          "bandwidth": this.lightSourceProps.bandwidth,
          "mean_photon_num": this.lightSourceProps.meanPhotonNum,
          "phase_error": this.lightSourceProps.phaseError,
        }
      };
      this.nodesData[nodesArray[i].key] = nodereq;
      if ((this.myDiagram.model.nodeDataArray[i] as any).key in this.nodesData) {
        this.nodes.push(this.nodesData[(this.myDiagram.model.nodeDataArray[i] as any).key])
      }
    }
    for (const [key, value] of Object.entries(this.nodesData)) {
      if (value["Type"].toLowerCase() == 'end') {
        this.endNodes.push(value)
      } else if (value["Type"].toLowerCase() == 'service') {
        this.serviceNodes.push(value)
      }
    }
    console.log("End Nodes:", this.endNodes)
    console.log("Service Nodes:", this.serviceNodes)
    if (this.endNodes.length != 0) {
      this.nodesSelection.sender = this.endNodes.length > 0 ? this.endNodes[0].Name : ""
      this.nodesSelection.receiver = this.endNodes.length > 1 ? this.endNodes[1].Name : this.endNodes[0].Name
      this.nodesSelection.endNode1 = this.endNodes.length > 0 ? this.endNodes[0].Name : ""
      this.nodesSelection.endNode2 = this.endNodes.length > 1 ? this.endNodes[1].Name : this.endNodes[0].Name
      this.nodesSelection.endNode3 = this.endNodes.length > 2 ? this.endNodes[2].Name : this.endNodes.length == 2
        ? this.endNodes[1].Name : this.endNodes[0].Name
    }
    if (this.serviceNodes.length != 0)
      this.nodesSelection.middleNode = this.serviceNodes.length > 0 ? this.serviceNodes[0].Name : ''
  }
  ngOnInit(): void {
    this.con.getAppList().pipe(map((d: any) => d.appList)).subscribe((result: any) => this.app_data = result);
    this.app_id = localStorage.getItem('app_id')
    this.application = localStorage.getItem('app')
    this.routeFrom = this.holdingData.getRoute();
    this.app = Number(localStorage.getItem('app_id'))
    this.simulator.options = this.app == 2 ? [{ header: 'Version 1', value: 'version1' }, { header: 'Version 2', value: 'version2' }] : [{
      header: 'Version 1', value: 'version1'
    }]
    this.debugOptions.moduleOptions = [
      {
        name: 'NETWORK', value: 'network'
      },
      {
        name: 'PHYSICAL', value: 'physical'
      },
      {
        name: 'LINK', value: 'link'
      }, {
        name: 'TRANSPORT', value: 'transport'
      },

      {
        name: 'APPLICATION', value: 'application'
      },
      {
        name: 'EVENT SIMULATION', value: 'eventSimulation'
      }
    ]
    this.debugOptions.loggingLevelOptions = [
      {
        name: 'DEBUG', value: 'debug'
      },
      {
        name: 'INFO', value: 'info'
      }
    ]
    this.subscription = this.diagramStorage.currentAdvancedFormData.subscribe(formData => {
      if (formData) {
        this.appSettingsForm = formData;
      } else {
        this.initForm();
      }
    });
  }
  changeApp() {
    localStorage.setItem("app_id", this.app)
    this.app_id = this.app
    this.simulator.options = this.app == 2 ? [{ header: 'Version 1', value: 'version1' }, { header: 'Version 2', value: 'version2' }] : [{
      header: 'Version 1', value: 'version1'
    }]
  }
  routeTo() {
    this._route.navigate(['/minimal'])
  }
  parameters() {
    this.app_id = localStorage.getItem('app_id')
    if (this.app_id == 5) {
      if (this.appSettingsForm.get('message')?.value.length % 2 != 0) {
        alert("Message length should be even ");
        // this.spinner = false
        return
      }
    }

    if (this.app_id == 10 || this.app_id == 9 || this.app_id == 7 || this.app_id == 6) {
      if (this.nodesSelection.message == '') {
        alert("Please select a message")
        return
      }
      if (this.nodesSelection.message.length % 2 != 0) {
        alert("Message length should be even ");
        return
      }
    }
    if (this.app_id == 8) {
      if (this.appSettingsForm.get('message1')?.value.length % 2 != 0) {
        alert("Message1 length should be even ");
        // this.spinner = false
        return
      }
      if (this.appSettingsForm.get('message2')?.value.length % 2 != 0) {
        alert("Message2 length should be even ");
        // this.spinner = false
        return
      }
    }
    if (this.app_id != 4) {
      if (this.nodesSelection.sender == '') {
        alert("Please select a sender")
        return
      }
      else if (this.nodesSelection.receiver == '') {
        alert("Please select a receiver.")
        return;
      }
      else if (this.nodesSelection.sender == this.nodesSelection.receiver) {
        alert("Sender and Receiver cannot be same node");
        return;
      }
    }
    if (this.app_id == 10) {
      if ((this.lightSourceProps.meanPhotonNum >= 0) && !(this.lightSourceProps.meanPhotonNum <= 1)) {
        alert("Mean Photon Number should be between 0 and 1");
        return
      }
    }
    if (this.app_id == 4) {
      let middleNode = this.appSettingsForm.get('middleNode')?.value
      //this.nodesSelection.endNode1)
      //this.nodesSelection.endNode2)
      //this.nodesSelection.endNode3)
      if (this.nodesSelection.endNode1 == '' || this.nodesSelection.endNode2 == '' || this.nodesSelection.endNode3 == '' || middleNode == '') {
        alert('Please select End Nodes.')
        return;
      }
      if (this.nodesSelection.endNode1 == this.nodesSelection.endNode2
        || this.nodesSelection.endNode2 == this.nodesSelection.endNode3
        || this.nodesSelection.endNode3 == this.nodesSelection.endNode1) {
        alert("End Nodes cannot be same node");
        return;
      }
    }
    if (this.myDiagram.model.nodeDataArray.length > 2) {
      if (this.myDiagram.model.nodeDataArray.every(obj => obj.properties[0].propValue === "End")) {
        alert("All elements are of type End");
        return;
      }
    }
    for (let i = 0; i < this.myDiagram.model.nodeDataArray.length; i++) {
      if (!((this.myDiagram.model.nodeDataArray[i] as any).key in this.nodesData)) {
        alert("Please configure the node named:" + (this.myDiagram.model.nodeDataArray[i] as any).text);
        return;
      };
    }
    this.myDiagram.model.modelData['position'] = go.Point.stringify(this.myDiagram.position);
    this.links = this.diagramBuilder.getQuantumConnections(this.myDiagram.model, this.detectorProps.powerLoss)
    this.nodes = []
    for (const [key, value] of Object.entries(this.nodesData)) {
      this.nodes.push(value)
    }
    // const fromNode = this.myDiagram.model.nodeDataArray.find(node => node.name == this.nodesSelection.sender);
    // console.log(fromNode)
    // const toNode = this.myDiagram.model.nodeDataArray.find(node => node.name == this.nodesSelection.receiver);
    // console.log(toNode);
    // const links = this.myDiagram.model.linkDataArray;
    // console.log(links)
    // const hasRoutes = links.some(link => link.from === fromNode.key && link.to === toNode.key);


    // let path = this.diagramBuilder.findRouteBFS(fromNode, toNode, this.myDiagram);
    // path = path.filter(link => link.from != null && link.to != null)
    // console.log(path);
    // } else {
    //   console.log("There are no routes between the nodes");
    // }

    this.spinner = true;
    this.app_id = localStorage.getItem('app_id')
    if (!this.app_id) {
      this._route.navigate(['/applications'])
    }
    this.app_id = Number(this.app_id)
    this.cc = []
    this.cc = this.holdingData.getClassicalConnections(this.nodes)
    this.topology = {
      nodes: this.nodes,
      quantum_connections: this.links,
      classical_connections: this.cc,
      detector: {
        efficiency: this.detectorProps.efficiency,
        count_rate: this.detectorProps.countRate,
        time_resolution: this.detectorProps.timeResolution,

      }
    }
    const appConfig =
    {
      1: {
        sender: this.nodesSelection.sender,
        receiver: this.nodesSelection.receiver,
        keyLength: Number(this.appSettingsForm.get('keyLength')?.value)
      },

      2: {
        sender: this.nodesSelection.sender,
        receiver: this.nodesSelection.receiver,
        startTime: 1e12,
        size: this.appSettingsForm.get('size')?.value,
        priority: 0,
        targetFidelity: this.e2e.targetFidelity,
        timeout: this.appSettingsForm.get('timeout')?.value + 'e12'
      }
      , 3: {
        sender: this.nodesSelection.sender,
        receiver: this.nodesSelection.receiver,
        amplitude1: this.appSettingsForm.get('amplitude1')?.value,
        amplitude2: this.appSettingsForm.get('amplitude2')?.value
      }, 4: {
        endnode1: this.appSettingsForm.get('endnode1')?.value,
        endnode2: this.appSettingsForm.get('endnode2')?.value,
        endnode3: this.appSettingsForm.get('endnode3')?.value,
        middlenode: this.appSettingsForm.get('middleNode')?.value,
      }, 5:
      {
        sender: this.nodesSelection.sender,
        receiver: this.nodesSelection.receiver,
        sequenceLength: this.appSettingsForm.get('sequenceLength')?.value,
        key: this.appSettingsForm.get('message')?.value
      }, 6:
      {

        sender: {
          node: this.nodesSelection.sender,
          message: this.nodesSelection.message,
          switchProb: this.nodesSelection.switchProb
        },
        receiver: {
          node: this.nodesSelection.receiver,
        },
        error_threshold: this.nodesSelection.errorThreshold,
        bell_type: `${this.nodesSelection.bellType}`,
        attack: this.nodesSelection.attack,
      }, 7:
      {
        sender: {
          node: this.nodesSelection.sender,
          message: this.nodesSelection.message,
          userID: `${this.nodesSelection.senderId}`,
          num_check_bits: this.nodesSelection.numCheckBits,
          num_decoy_photons: this.nodesSelection.numDecoy
        },
        receiver: {
          node: this.nodesSelection.receiver,
          userID: `${this.nodesSelection.receiverId}`
        },
        bell_type: `${this.nodesSelection.bellType}`,
        attack: this.nodesSelection.attack,
      },
      8:
      {
        sender: this.nodesSelection.sender,
        receiver: this.nodesSelection.receiver,
        message1: this.appSettingsForm.get('message1')?.value,
        message2: this.appSettingsForm.get('message2')?.value,
        attack: ''
      }, 9:
      {
        sender: {
          node: this.nodesSelection.sender,
          message: this.nodesSelection.message,
        },
        receiver: {
          node: this.nodesSelection.receiver,
        },
        bell_type: `${this.nodesSelection.bellType}`,
        attack: this.nodesSelection.attack,

      }, 10:
      {
        sender: {
          node: this.nodesSelection.sender,
          message: this.nodesSelection.message,
          userID: `${this.nodesSelection.senderId}`,
          num_check_bits: this.nodesSelection.numCheckBits,
          num_decoy_photons: this.nodesSelection.numDecoy
        },
        receiver: {
          node: this.nodesSelection.receiver,
          userID: `${this.nodesSelection.receiverId}`
        },
        bell_type: `${this.nodesSelection.bellType}`,
        error_threshold: this.nodesSelection.errorThreshold,
        attack: this.nodesSelection.attack,
        channel: this.nodesSelection.channel
      }
    }
    this.appSettings = appConfig[this.app_id]
    this.debug.modules = this.debug.modules.map(module => module.value);

    var req = {
      "application": this.app_id,
      "topology": this.topology,
      "appSettings": this.appSettings,
      "debug": {
        "modules": this.debug.modules,
        "logLevel": this.debug.loggingLevel.value,
      }
    }
    let url = this.app_id != 2
      ? environment.apiUrl
      : this.simulator.value == 'version1'
        ? environment.apiUrl
        : environment.apiUrlNew;
    // let url = environment.apiUrlNew;
    // this.apiService.getStream().subscribe(data => { this.logs = data; });
    // whatever your request data is
    // The API service is used to send the request to the backend
    this.apiService.advancedRunApplication(req, url).subscribe({
      next: (response) => {
        this.con.setResult(response);
        if (response.application.Err_msg) {
          alert(`Error has occurred!! ${response.application.Err_msg}`)
        }
      },
      error: (error) => {
        console.error(`Error: ${error}`);
        this.spinner = false;
        alert(`Error has occurred! Status Code:${error.status} Status Text:${error.statusText}`)
      },
      complete: () => {
        this.spinner = false;
        sessionStorage.setItem("saved_model", this.myDiagram.model)
        this._route.navigate(['/results'])
      }
    });
  }
  linkClicked(link: any) {
    if (!link || !link.data || !link.data.key) {
      console.error("Invalid link detected: ", link);
      return;
    }
    this.linksProps.keySelected = link.data.key;
    this.linksProps.attenuation = this.linkData[this.linksProps.keySelected].attenuation;
    this.linksProps.distance = this.linkData[this.linksProps.keySelected].distance;
    this.isLinkParameters = true;
  }
  linkSaved() {
    //"link Saved", this.linksProps.keySelected)
    // this.linkData[this.linksProps.keySelected] = { distance: this.linksProps.distance, attenuation: this.linksProps.distance, ...this.linkData[this.linksProps.keySelected] }
    this.linkData[this.linksProps.keySelected].distance = this.linksProps.distance
    this.linkData[this.linksProps.keySelected].attenuation = this.linksProps.attenuation
    //"LinkSaved", this.linkData)
    this.isLinkParameters = false
  }
  addNode(nodetype: string) {
    var adornedPart = this.adornedpart
    const newKey = this.myDiagram.model.nodeDataArray[this.myDiagram.model.nodeDataArray.length - 1].key
    const linkKey = this.myDiagram.model.linkDataArray.length > 0 ? this.myDiagram.model.linkDataArray[this.myDiagram.model.linkDataArray.length - 1].key : 0;
    const newNode = this.diagramBuilder.addNewNode(nodetype, newKey)
    const newLink = this.diagramBuilder.addNewLink(linkKey, adornedPart, newNode)
    this.myDiagram.startTransaction('Add node and link');
    this.myDiagram.model.addNodeData(newNode);
    this.myDiagram.model.addLinkData(this.diagramBuilder.addNewLink(linkKey, adornedPart, newNode));
    this.myDiagram.commitTransaction('Add node and link');
    this.linkData[newLink.key] = newLink
    this.myDiagram.zoomToFit();
    this.nodeTypeSelect = false
    this.updateNodes()
  }
  drawLink(e, part) {
    var node = part;
    console.log("drawLink", node)
    if (this.linkConnection.key == -1) {
      let linkKey = this.myDiagram.model.linkDataArray.length > 0 ? this.myDiagram.model.linkDataArray.at(-1).key : 0;
      this.linkConnection.key = linkKey + 1
    }
    if (this.linkConnection.from == -1) {
      this.linkConnection.from = node.data.key
      console.log("added from node")
    }
    if (this.linkConnection.to == -1 && this.linkConnection.from != node.data.key) {
      this.linkConnection.to = node.data.key
      console.log("added to node")
    }
    if (this.linkConnection.from != -1 && this.linkConnection.to != -1) {
      if (this.diagramBuilder.isDirectLinkExists(this.linkConnection.from, this.linkConnection.to, this.myDiagram)) {
        this.myDiagram.startTransaction('Add link');
        this.myDiagram.model.addLinkData(this.linkConnection);
        this.myDiagram.commitTransaction('Add link');
        this.myDiagram.zoomToFit();
        this.linkConnection = {
          key: -1,
          from: -1,
          to: -1,
          distance: 70,
          attenuation: 0.0001
        }
        console.log("link Added!!!")
      }
      else {
        this.linkConnection = {
          key: -1,
          from: -1,
          to: -1,
          distance: 70,
          attenuation: 0.0001
        }
        alert("Link already exists!!");
        return;
      }
    }
    // console.log(this.linkConnection)
  }
  activeindex(data: string) {
    // if the data is 'next' then the active index is incremented by 1
    if (data == 'next') {
      if (this.activeIndex <= 1) {
        this.activeIndex++;
      }
      // if the data is 'prev' then the active index is decremented by 1
    } else if (data == 'prev') {
      if (this.activeIndex >= 1) {
        this.activeIndex--;
      }
    }
  }
  // Define a method to delete a node
  deleteNode(nodeData: any) {
    const diagram = this.myDiagram;
    if (diagram.model.nodeDataArray.length > 1) {
      diagram.startTransaction('delete node');
      // find the node in the diagram by its data
      const node = diagram.findNodeForData(nodeData);
      // remove the node from the diagram
      diagram.remove(node);
      diagram.commitTransaction('delete node');
      this.myDiagram.zoomToFit();
    }
    this.updateNodes()
  }

  get middlenode() {
    return this.appSettingsForm.get('middleNode')
  }
  get keyLength() {
    return this.appSettingsForm.get('keyLength')
  }
  get key() {
    return this.appSettingsForm.get('key')
  }
  numericOnly(event): boolean {
    const charCode = (event.which) ? event.which : event.keyCode;
    if (charCode !== 48 && charCode !== 49 && charCode !== 96 && charCode !== 97 && charCode !== 8 && charCode !== 9) {
      return false;
    }
    return true;
  }
  initDiagram() {
    const $ = go.GraphObject.make;
    this.myDiagram = $(go.Diagram, this.diagramRef.nativeElement, {
      initialContentAlignment: go.Spot.Center,
      'undoManager.isEnabled': true,
      'initialAutoScale': go.Diagram.Uniform, // Ensures the myDiagram fits the viewport
      "linkingTool.isEnabled": false,  // invoked explicitly by drawLink function, below
      "linkingTool.direction": go.LinkingTool.ForwardsOnly,  // only draw "from" towards "to"
      'allowZoom': true, // Disables zooming
      layout: $(go.ForceDirectedLayout)
    });
    function isPositiveNumber(val: any) {
      //val)
      const regex = /^\d+$/;
      return regex.test(val);
    }
    function isDecimalNumber(val: any): boolean {
      const regex = /^\d+(\.\d*)?$/;
      if (regex.test(val)) {
        val = Number(val)
        if (val >= 0 && val <= 1) {
          return true;
        }
      };
      return false;
    }
    function isFloat(val: any): boolean {
      const regex = /^\d+(\.\d*)?$/;
      return regex.test(val) ? true : false
    }
    function isNodeTypeValid(val: string): boolean {
      // if val is not equal to 'service' AND val is not equal to 'end' AND val is not equal to 'Service' AND val is not equal to 'End'
      if (val != 'service' && val != 'end' && val != 'Service' && val != 'End') {
        // return false
        return false
      }
      // return true
      return true
    }
    function capitalizethefirstletter(word) {
      return word.charAt(0).toUpperCase() + word.slice(1);
    }

    var memoryTemplate =
      $(go.Panel, "Horizontal",
        $(go.TextBlock,
          { isMultiline: false, editable: false },
          new go.Binding("text", "propName").makeTwoWay(),
          new go.Binding("isUnderline", "scope", s => s[0] === 'c')
        ),
        // property type, if known
        $(go.TextBlock, "",
          new go.Binding("text", "propValue", t => t ? ": " : "")),
        $(go.Panel, "Auto",
          $(go.Shape, "RoundedRectangle", { fill: "white" }),
          $(go.TextBlock,
            { margin: 1, isMultiline: false, editable: true },
            new go.Binding("text", "propValue").makeTwoWay()
          )
        ),
        // property default value, if any
        $(go.TextBlock,
          { isMultiline: false, editable: false },
          new go.Binding("text", "default", s => s ? " = " + s : "")
        )
      );
    var propertyTemplate =
      $(go.Panel, "Horizontal",
        $(go.TextBlock,
          { isMultiline: false, editable: false },
          new go.Binding("text", "propName").makeTwoWay(),
          new go.Binding("isUnderline", "scope", s => s[0] === 'c')
        ),
        // property type, if known
        $(go.TextBlock, "",
          new go.Binding("text", "propValue", t => t ? ": " : "")),
        $(go.Panel, "Auto",
          $(go.Shape, "RoundedRectangle", { fill: "white" }),
          $(go.TextBlock,
            { margin: 1, isMultiline: false, editable: true },
            new go.Binding("text", "propValue").makeTwoWay()
          )
        ),
        // property default value, if any
        $(go.TextBlock,
          { isMultiline: false, editable: false },
          new go.Binding("text", "default", s => s ? " = " + s : "")
        )
      );

    this.myDiagram.nodeTemplate =
      $(go.Node, "Auto",
        {
          locationSpot: go.Spot.Center,
          fromSpot: go.Spot.AllSides,
          toSpot: go.Spot.AllSides,
          selectionAdornmentTemplate:
            $(go.Adornment, "Spot",
              $(go.Panel, "Auto",
                $(go.Shape, { stroke: "dodgerblue", strokeWidth: 2, fill: null }),
                $(go.Placeholder)
              )
            ),

          click: (event, node: any) => { if (this.linkConnection.from !== -1) this.drawLink(event, node); },
          mouseEnter: function (e, node: any) {
            node.isSelected = true;
          },
          mouseLeave: function (e, node: any) {
            setTimeout(() => { node.isSelected = false; }, 2000)
          },
        },
        $(go.Shape, "RoundedRectangle", { strokeWidth: 1, stroke: "black" },
          // Shape.fill is bound to Node.data.color
          new go.Binding("fill", "color"),
        ),
        $(go.Panel, "Table",
          { defaultRowSeparatorStroke: "black" },
          // header
          $(go.TextBlock,
            {
              row: 0, columnSpan: 2, margin: 3, alignment: go.Spot.Center,
              font: "bold 12pt sans-serif",
              isMultiline: false, editable: true
            },
            new go.Binding("text", "name").makeTwoWay()),

          // properties
          $(go.TextBlock, "Properties",
            { row: 1, font: "italic 10pt sans-serif" },
            new go.Binding("visible", "visible", v => !v).ofObject("PROPERTIES")),
          $(go.Panel, "Vertical", { name: "PROPERTIES" },
            new go.Binding("itemArray", "properties"),
            {
              row: 1, margin: 3, stretch: go.GraphObject.Fill,
              defaultAlignment: go.Spot.Left, background: "lightblue",
              itemTemplate: propertyTemplate
            }, new go.Binding("background", "color")
          ),
          $("PanelExpanderButton", "PROPERTIES",
            { row: 1, column: 1, alignment: go.Spot.TopRight, visible: false },
            new go.Binding("visible", "properties", arr => arr.length > 0)),
          // methods
          $(go.TextBlock, "Memory",
            { row: 2, font: "italic 10pt sans-serif" },
            new go.Binding("visible", "visible", v => !v).ofObject("MEMORY")),
          $(go.Panel, "Vertical", { name: "MEMORY" },
            new go.Binding("itemArray", "memory"),
            {
              row: 2, margin: 3, stretch: go.GraphObject.Fill,
              defaultAlignment: go.Spot.Left, background: "lightblue",
              itemTemplate: memoryTemplate
            },
            new go.Binding("background", "color"),
            new go.Binding("visible", "isVisible")
          ),
          $("PanelExpanderButton", "MEMORY",
            { row: 2, column: 1, alignment: go.Spot.TopRight, visible: true },
            new go.Binding("visible", "memory", arr => arr.length > 0)),
          $(go.Panel, 'Spot',
            {
              alignment: go.Spot.Right,
              alignmentFocus: go.Spot.Left,
              click: (e: any, obj: any) => this.selectNodeType(obj.part)
            },
            $(go.Shape,
              {
                figure: 'Rectangle',
                spot1: new go.Spot(0, 0, 4, 0), spot2: new go.Spot(1, 1, -1, -1),
                fill: 'transparent', strokeWidth: 0,
                desiredSize: new go.Size(20, 20),
                margin: new go.Margin(0, 0, 0, 20),
                mouseEnter: (e: any, obj: any) => {
                  // obj.fill = 'rgba(128,128,128,0.7)';
                },
                mouseLeave: (e: any, obj: any) => {
                  // obj.fill = 'lighblue';
                }
              }
            ),
            $(go.TextBlock, '+', { font: 'bold 10pt sans-serif', margin: new go.Margin(0, 0, 0, 5) })
          ),
          $(go.Panel, "Spot",
            {
              alignment: go.Spot.Left,
              alignmentFocus: go.Spot.Right,
              click: (e: any, obj: any) => this.deleteNode(obj.part.data)
            },
            $(go.Shape,
              {
                figure: 'Rectangle',
                spot1: new go.Spot(0, 0, 0, 1), spot2: new go.Spot(1, 1, -1, -1),
                fill: 'transparent', strokeWidth: 0,
                desiredSize: new go.Size(30, 30),
                margin: new go.Margin(0, 0, 0, 2),
                mouseEnter: (e: any, obj: any) => {
                  // obj.fill = 'lightblue';
                },
                mouseLeave: (e: any, obj: any) => {
                  // obj.fill = 'lightblue';
                }
              }
            ),
            $(go.TextBlock, '-', { font: 'bold 10pt sans-serif', margin: new go.Margin(0, 5, 0, 0) })
          )
        )
      );
    this.myDiagram.nodeTemplate.selectionAdornmentTemplate =
      $(go.Adornment, "Spot",
        $(go.Panel, "Auto",
          $(go.Shape, { stroke: "dodgerblue", strokeWidth: 2, fill: null }),
          $(go.Placeholder)
        ),
        $(go.Panel, "Horizontal",
          { alignment: go.Spot.Right, alignmentFocus: go.Spot.Bottom },

          $("Button",
            { // drawLink is defined below, to support interactively drawing new links
              click: (event, button: any) => { this.drawLink(event, button.part.adornedPart) },  // click on Button and then click on target node
              // actionMove: drawLink  // drag from Button to the target node
            },
            $(go.Shape,
              { geometryString: "M0 0 L8 0 8 12 14 12 M12 10 L14 12 12 14" })
          )
        )
      );
    // define the Link template
    this.myDiagram.linkTemplate =
      $(go.Link,
        {
          click: (e, link) => {  // click event handler
            this.linkClicked(link);
          },
          selectionAdorned: false,
          contextMenu: $(
            go.Adornment,
            "Vertical",
            $(
              "ContextMenuButton",
              $(go.TextBlock, "Delete"),
              {
                click: (e, obj: any) => {
                  const link = obj.part.adornedPart;
                  if (link instanceof go.Link) {
                    this.myDiagram.model.removeLinkData(link.data);
                  }
                },
              }
            )
          ),
        },
        new go.Binding("routing", "routing"),
        $(go.Shape),
        $(go.Shape, { toArrow: 'Standard' })
      );

    var nodeDataArray
    var linkDataArray
    // if advancedDiagramModel is defined then we want to use that model to 
    // render the diagram
    if (this.diagramStorage.getAdvancedDiagramModel()) {
      nodeDataArray = this.diagramStorage.advancedDiagramModel.nodeDataArray
      linkDataArray = this.diagramStorage.advancedDiagramModel.linkDataArray
    } else {
      // otherwise we want to use a basic model
      nodeDataArray = [
        {
          key: 1,
          name: "node1",
          color: "lightblue",
          properties: [
            {
              propName: "Type",
              propValue: "End",
              nodeType: true
            },
            {
              propName: "No of Memories",
              propValue: 500,
              numericValueOnly: true
            }
          ],
          memory: [
            {
              propName: "Memory Frequency (Hz)",
              propValue: 8e7,
              numericValueOnly: true
            },
            {
              propName: "Memory Expiry (s)",
              propValue: 100,
              float: true
            },
            {
              propName: "Memory Efficiency",
              propValue: 1,
              decimalValueAlso: true
            },
            {
              propName: "Memory Fidelity",
              propValue: 0.93,
              decimalValueAlso: true
            }
          ],
          isVisible: false
        }
      ]
      linkDataArray = []
    }

    this.myDiagram.model = new go.GraphLinksModel(nodeDataArray, linkDataArray);
    this.myDiagram.addDiagramListener("LayoutCompleted", (e) => {
      this.myDiagram.findTopLevelGroups().each((group) => {
        if (group.findObject("MEMORY")) {
          group.findObject("MEMORY").collapse();
        }
      });
      this.updateNodes()
    });
    // When a user edits a text block, check if the text block belongs to a node
    // and if the node has properties or memory
    this.myDiagram.addDiagramListener("TextEdited", (e: any) => {
      const tb = e.subject;
      const nodeData = tb.part && tb.part.data;
      if (nodeData && nodeData.properties) {
        // If the node has properties, check if the edited text matches the text of a property
        const editedProperty = nodeData.properties.find((prop: any) => prop.propValue.toString() === tb.text);
        //editedProperty)
        // If the property is numeric and the edited text is not a positive number, revert the text to the previous value
        if (editedProperty && editedProperty.numericValueOnly) {
          if (!isPositiveNumber(tb.text)) {
            tb.text = e.parameter; // Revert to the previous text value
          }
        }
        // If the property is a node type and the edited text is not a valid node type, revert the text to the previous value
        if (editedProperty && editedProperty.nodeType) {
          if (isNodeTypeValid(tb.text)) {
            tb.text = capitalizethefirstletter(tb.text)
            const color = tb.text.toLowerCase() == 'service' ? "lightsalmon" : tb.text.toLowerCase() === 'end' ? 'lightblue' : ''

            this.myDiagram.model.setDataProperty(nodeData, "color", color);
            // this.myDiagram.model.setDataProperty(nodeData, "color", color);
            // if (tb.text.toLowerCase() === 'service') {
            //   // tb.text = capitalizethefirstletter(tb.text)
            //   const nodeIndex = this.myDiagram.model.nodeDataArray.findIndex((node: any) => node.key == nodeData.key)
            //   let modifiedNodeData = this.diagramBuilder.addSwapSuccessInMemory(nodeData, this.myDiagram)

            //   console.log("Replace Node", nodeData)
            //   this.myDiagram.startTransaction("replaceNode");
            //   this.myDiagram.model.nodeDataArray[nodeIndex] = modifiedNodeData;
            //   this.myDiagram.commitTransaction("replaceNode");
            //   // this.myDiagram.model.setDataProperty(newNode, "color", color);
            //   console.log("Replace Node Completed", this.myDiagram.model.nodeDataArray[nodeIndex])
            // }
            // else if (tb.text.toLowerCase() === 'end') {
            //   // tb.text = capitalizethefirstletter(tb.text)
            //   const nodeIndex = this.myDiagram.model.nodeDataArray.findIndex((node: any) => node.key == nodeData.key)
            //   let modifiedNodeData = this.diagramBuilder.removeSwapSuccessInMemory(nodeData, this.myDiagram)
            //   console.log("Replace Node")
            //   this.myDiagram.startTransaction("replaceNode");
            //   this.myDiagram.model.nodeDataArray[nodeIndex] = modifiedNodeData;
            //   this.myDiagram.commitTransaction("replaceNode");
            //   // this.myDiagram.model.setDataProperty(newNode, "color", color);
            //   console.log("Replace Node Completed")
            // }
          }
          else {
            tb.text = e.parameter
          }
        }
      }
      // If the node has memory, check if the edited text matches the text of a memory property
      if (nodeData && nodeData.memory) {
        const editedProperty = nodeData.memory.find((prop: any) => prop.propValue.toString() === tb.text);
        // //editedProperty)
        // If the property is decimal and the edited text is not a decimal, revert the text to the previous value
        if (editedProperty && editedProperty.decimalValueAlso) {
          if (!isDecimalNumber(tb.text)) {
            tb.text = e.parameter; // Revert to the previous text value
          }
        }
        // If the property is numeric and the edited text is not a positive number, revert the text to the previous value
        if (editedProperty && editedProperty.numericValueOnly) {
          if (!isPositiveNumber(tb.text)) {
            tb.text = e.parameter; // Revert to the previous text value
          }
        }
        // If the property is a float and the edited text is not a float, revert the text to the previous value
        if (editedProperty && editedProperty.float) {
          // //"Is float:" + isFloat(tb.text))
          if (!isFloat(tb.text)) {
            // //"Text:" + tb.text)
            tb.text = e.parameter;
          }
        }
      }
      this.updateNodes()
    });
    this.myDiagram.addDiagramListener("Modified", () => {
      this.diagramStorage.setAdvancedDiagramModel(this.myDiagram.model)
      this.updateNodes
    });


    // this.myDiagram.addDiagramListener("ObjectSingleClicked", function (e) {
    //   var part = e.subject.part;
    //   if (part instanceof go.Node) {
    //     console.log(part)
    //   }
    // });
  }
  public zoomIn() {
    const diagram = this.myDiagram;
    const zoom = diagram.commandHandler.zoomFactor;
    diagram.commandHandler.zoomTo(zoom + 0.1, diagram.lastInput.documentPoint);
  }

  public zoomOut() {
    const diagram = this.myDiagram;
    const zoom = diagram.commandHandler.zoomFactor;
    diagram.commandHandler.zoomTo(Math.max(zoom - 0.1, 0.1), diagram.lastInput.documentPoint);
  }
  initForm() {
    this.appSettingsForm = this.fb.group({
      'sender': ['', Validators.required],
      'receiver': ['', Validators.required],
      'startTime': new FormControl('1'),
      'size': new FormControl('6'),
      'targetFidelity': new FormControl('0.5'),
      'timeout': new FormControl('1'),
      'keyLength': new FormControl('5'),
      'message': new FormControl('10011100', evenLengthValidator),
      'sequenceLength': new FormControl('2'),
      'amplitude1': new FormControl('0.70710678118+0j'),
      'amplitude2': new FormControl('0-0.70710678118j'),
      'endnode1': new FormControl(''),
      'endnode2': new FormControl(''),
      'endnode3': new FormControl(''),
      'middleNode': new FormControl(''),
      'message1': new FormControl('hello'),
      'message2': new FormControl('world'),
      'num_photons': new FormControl(''),
      'inputMessage': new FormControl(''),
      'ip2message': new FormControl(''),
      'senderId': new FormControl('1010'),
      'receiverId': new FormControl('1011'),
      'numCheckBits': new FormControl(''),
      'numDecoy': new FormControl(''),
      'attack': new FormControl(''),
      'belltype': [],
      'channel': [],
      'errorthreshold': []
    })
  }
}
// This code is used to validate that the length of a string is even.
// It is used in the form to ensure that the length of the first name is even.
// It is used in the form to ensure that the length of the last name is even.

// create a validator function
function evenLengthValidator(control: FormControl) {
  // get the value of the control
  const value = control.value;
  // if the value is not even, return an object with an error name
  if (value.length % 2 !== 0) {
    return { evenLength: true };
  }
  // otherwise, return null (no error)
  return null;
}

