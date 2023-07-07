import { Component, OnDestroy, OnInit, ViewEncapsulation } from '@angular/core';
import { MenuItem } from 'primeng/api';
import { Router } from '@angular/router';
import { HoldingDataService } from 'src/services/holding-data.service';

@Component({
  selector: 'app-intro',
  templateUrl: './intro.component.html',
  styleUrls: ['./intro.component.less'],
  encapsulation: ViewEncapsulation.None,
})
export class IntroComponent implements OnInit, OnDestroy {
  items: MenuItem[];
  activeIndex = 0;
  step = 1;
  app: any;
  tel = new Teleportation();
  e2e = new E2E();
  routeFrom: string;
  constructor(private router: Router, private holding: HoldingDataService) { }
  ngOnDestroy(): void {
    this.holding.setRoute('')
  }
  ngOnInit(): void {
    this.routeFrom = this.holding.getRoute();
    console.log(this.routeFrom)
    this.app = localStorage.getItem('app_id');
    this.initItems();
  }
  route() {
    this.router.navigate(['/minimal'])
  }
  initItems() {
    const baseItems = [
      { label: 'Sharing Bell States', index: 1 },
      { label: 'Measurement', index: 2 },
      { label: 'Revealing the bases', index: 3 },
      // Add more labels as needed
    ];

    this.items = baseItems.map(item => ({
      label: item.label,
      command: () => console.log(item.index),
    }));
  }

  updateIndex(val: number) {
    this.activeIndex += val;
    this.step = val > 0 ? 1 : 2;
    window.scroll({ top: 0, behavior: 'smooth' });
  }

  previous() { this.updateIndex(-1); }
  next() { this.updateIndex(1); }

  changeStep(val: number) {
    this.step += val;
    window.scroll({ top: 0, behavior: 'smooth' });
  }
  goto() {
    this.router.navigate(['/advanced'])
  }
  previousStep() { this.changeStep(-1); }
  nextStep() { this.changeStep(1); }
  quant_ph(url: string) { window.open(url, "_blank"); }
}

export class Teleportation {
  tel1: string;
  tel2: string;
  tel3: string;
}
export class E2E {
  e2e1: string;
  e2e2: string;
  e2e3: string;
}
