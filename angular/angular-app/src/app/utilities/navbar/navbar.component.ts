import { AfterViewInit, Component, HostListener, Input, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { ConditionsService } from 'src/services/conditions.service';

@Component({
  selector: 'app-navbar',
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.less']
})
export class NavbarComponent implements OnInit, AfterViewInit {
  // loggedIn: boolean
  @Input() list: []
  currentSection: any = this.conService.currentSection
  constructor(private conService: ConditionsService, private router: Router) { }
  ngAfterViewInit(): void {
  }
  late = "0px 8px 8px -6px rgba(0, 0, 0, .5)"
  ngOnInit(): void {
  }
  home() {
    this.router.navigate(['/']);
  }

}
