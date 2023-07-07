import { ViewEncapsulation } from '@angular/core';
import { AfterViewInit, Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { MenuItem } from 'primeng/api';
import { ConditionsService } from 'src/services/conditions.service';
@Component({
  selector: 'app-results',
  templateUrl: './results.component.html',
  styleUrls: ['./results.component.less'],
  encapsulation: ViewEncapsulation.None
})
export class ResultsComponent implements OnInit, AfterViewInit {
  nodeData: any
  performance: any
  match: any = []
  alice_r: any
  app_id: any
  items: MenuItem[];
  activeItem: MenuItem;
  data: any
  keyGen: boolean
  keyBits: boolean
  cols: any
  logs: any
  app: string;
  constructor(private con: ConditionsService,
    private router: Router) { }
  ngAfterViewInit(): void {
  }
  ngOnInit(): void {
    this.app_id = Number(localStorage.getItem('app_id'))
    console.log(`APP ID: ${this.app_id}`)
    if (!this.app_id) {
      this.router.navigate(['/'])
    }
    this.performance = this.con.getResult().performance
    this.performance.execution_time = this.performance.execution_time.toFixed(3);
    this.performance.fidelity = this.performance.fidelity.toFixed(3)
    this.performance.latency = this.performance.latency.toFixed(3);
    this.data = this.con.getResult().application;
    this.logs = this.con.getResult().logs
    console.log(this.data, this.performance)
    if (this.app_id == 1) {
      this.match = this.data.sender_basis_list.reduce((match: any, x: any, i: any) => {
        if (x === this.data.receiver_basis_list[i]) match.push(i);
        return match;
      }, []);
      this.data.sender_keys = this.data.sender_keys.join('');
      this.data.receiver_keys = this.data.receiver_keys.join('');
    }
    else if (this.app_id == 7) {
      var alice = "Alice_r" + " "
      this.alice_r = this.data[alice]
    }
  }
  senderbasis(index: any) {
    var bool = this.match.includes(index)
    return bool ? "table-success" : "";
  }
  downloadTxtFile() {
    const arrayData = this.logs.join('\n')
    const blob = new Blob([arrayData], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    var anchor = document.createElement('a');
    anchor.download = 'logs.log';
    anchor.href = url;
    anchor.click();
  }

}
