import { Component, OnInit } from '@angular/core';
import {Router} from '@angular/router';

@Component({
  selector: 'app-navbar',
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.scss']
})
export class NavbarComponent implements OnInit {
  isOpen = false;
  isNavbarCollapsed = true;

  constructor(private router: Router) { }

  ngOnInit(): void {
  }

  onMenu(): void {
    this.isNavbarCollapsed = !this.isNavbarCollapsed;
    this.isOpen = !this.isOpen;
  }
}
