import {Component, OnInit} from '@angular/core';
import {Router} from '@angular/router';
import {AuthService} from '../../@service/security/auth.service';
import {Observable} from 'rxjs';
import {User} from '../../@model/user.model';
import {Constant} from '../app.constant';

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
    const user: User = this.authService.getUser() as User;
    return user ? user.displayName : '';
  }

  getUserAvatar(): string {
    const user: User = this.authService.getUser() as User;
    return Constant.DISCORD_BASE_IMG + 'avatars/' + user.providerUserId + '/' + user.avatar + '.png';
  }

  onSignOut(): void {
    this.authService.signOut();
    this.router.navigateByUrl('/login');
  }
}
