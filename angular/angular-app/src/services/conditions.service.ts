import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { map, Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ConditionsService {
  public app_id: number = 2
  public app: string
  currentSection: any;
  public selectedAppResult = new Subject();
  public _result = this.selectedAppResult.asObservable();
  constructor(private http: HttpClient) { }
  updateNode(value: any) {
    this.selectedAppResult.next(value)
  }
  public result: any

  getResult() {
    return this.result;
    // return this.dummytext
  }
  setResult(value: any) {
    this.result = value
  }
  getapp_id() {
    return this.app_id
  }
  setapp_id(app_id: number) {
    this.app_id = app_id
  }
  getApp() {
    return this.app
  }
  setApp(app: string) {
    this.app = app
  }
  jsonUrl(type: any, level: any) {
    return {
      url: type.toLowerCase() + '_' + level + '.json',
      type: type.toLowerCase()
    }
  }
  getJson(url: string, type: any) {
    return this.http.get('../assets/preload-topologies/' + type + '/' + url)
  }
  getAppList() {
    return this.http.get('../assets/app-infos/appList.json')
  }
  getAppSetting() {
    return this.http.get('../assets/app-infos/appSettings.json')
  }
  getMemory() {
    return { "frequency": 2000, "expiry": -1, "efficiency": 1, "fidelity": 0.93 }
  }


  dummytext = {

    "application": {

      "sender": [

        [

          0,

          "n1",

          "n3",

          0.6332,

          1.038,

          2000,

          "ENTANGLED"

        ],

        [

          1,

          "n1",

          "n3",

          0.6332,

          1.118,

          2000,

          "ENTANGLED"

        ],

        [

          2,

          "n1",

          "n3",

          0.6332,

          1.134,

          2000,

          "ENTANGLED"

        ],

        [

          3,

          "n1",

          "n3",

          0.6332,

          1.15,

          2000,

          "ENTANGLED"

        ],

        [

          4,

          "n1",

          "n3",

          0.6332,

          1.102,

          2000,

          "ENTANGLED"

        ]

      ],

      "receiver": [

        [

          0,

          "n3",

          "n1",

          0.6331666666666667,

          1.03800017501,

          2001.03800017501,

          "ENTANGLED"

        ],

        [

          1,

          "n3",

          "n1",

          0.6331666666666667,

          1.11800017501,

          2001.11800017501,

          "ENTANGLED"

        ],

        [

          2,

          "n3",

          "n1",

          0.6331666666666667,

          1.13400017501,

          2001.13400017501,

          "ENTANGLED"

        ],

        [

          3,

          "n3",

          "n1",

          0.6331666666666667,

          1.10200017501,

          2001.10200017501,

          "ENTANGLED"

        ],

        [

          4,

          "n3",

          "n1",

          0.6331666666666667,

          1.15000017501,

          2001.15000017501,

          "ENTANGLED"

        ]

      ]

    },

    "performance": {

      "latency": 0.10200017500999992,

      "fidelity": 0.6331666666666667,

      "throughput": 100.0,

      "execution_time": 5.79

    },

    "logs": [

      "INFO: Logging Begins...",

      "INFO: In e2e",

      "INFO: Creating request...",

      "INFO: Timeline start simulation",

      "INFO: ['n1', 'n2', 'n3']",

      "INFO: Swapping sucessful between ('n1', 'n3')",

      "INFO: Swapping sucessful between ('n1', 'n3')",

      "INFO: Entanglement failed between ('n2', 'n1')",

      "INFO: Entanglement failed between ('n1', 'n2')",

      "INFO: Entanglement failed between ('n3', 'n2')",

      "INFO: Entanglement failed between ('n2', 'n3')",

      "INFO: Entanglement failed between ('n2', 'n1')",

      "INFO: Entanglement failed between ('n1', 'n2')",

      "INFO: Entanglement failed between ('n2', 'n3')",

      "INFO: Entanglement failed between ('n3', 'n2')",

      "INFO: Entanglement failed between ('n2', 'n1')",

      "INFO: Entanglement failed between ('n1', 'n2')",

      "INFO: Entanglement failed between ('n2', 'n3')",

      "INFO: Entanglement failed between ('n3', 'n2')",

      "INFO: Swapping sucessful between ('n1', 'n3')",

      "INFO: Swapping sucessful between ('n1', 'n3')",

      "INFO: Swapping sucessful between ('n1', 'n3')",

      "INFO: Swapping sucessful between ('n1', 'n3')",

      "INFO: Swapping sucessful between ('n1', 'n3')",

      "INFO: Swapping sucessful between ('n1', 'n3')",

      "INFO: Swapping sucessful between ('n1', 'n3')",

      "INFO: Swapping sucessful between ('n1', 'n3')"

    ]

  }

}
