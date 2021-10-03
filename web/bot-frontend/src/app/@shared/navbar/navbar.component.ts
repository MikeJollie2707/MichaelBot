import {Component, OnInit} from '@angular/core';
import {Router} from '@angular/router';
import {AuthService} from '../../@service/security/auth.service';
import {Observable} from 'rxjs';

@Component({
  selector: 'app-navbar',
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.scss']
})
export class NavbarComponent implements OnInit {
  isOpen = false;
  isNavbarCollapsed = true;
  isLoggedIn: Observable<boolean> = new Observable<boolean>();

  constructor(private router: Router, private authService: AuthService) { }

  ngOnInit(): void {
    this.isLoggedIn = this.authService.isAuthChanged.asObservable();
  }

  onMenu(): void {
    this.isNavbarCollapsed = !this.isNavbarCollapsed;
    this.isOpen = !this.isOpen;
  }

  getUsername(): string {
    const user = this.authService.getUser();
    return user ? user.displayName : '';
  }

  onSignOut(): void {
    this.authService.signOut();
    this.router.navigateByUrl('/login');
  }
}
