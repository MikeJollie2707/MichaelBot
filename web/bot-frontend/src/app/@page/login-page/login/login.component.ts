import { Component, OnInit } from '@angular/core';
import {AuthService} from '../../../@service/security/auth.service';
import {ActivatedRoute} from '@angular/router';
import {UserApiService} from '../../../@service/api/user-api.service';
import {Observable} from 'rxjs';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {
  isLoggedIn: Observable<boolean> = new Observable<boolean>();
  errorMessage = '';
  currentUser: any;
  discordURL = 'http://localhost:8080/oauth2/authorization/discord?redirect_uri=http://localhost:4200/login';

  constructor(private authService: AuthService,
              private userApiService: UserApiService,
              private route: ActivatedRoute) {}

  ngOnInit(): void {
    this.isLoggedIn = this.authService.isAuthChanged.asObservable();

    const token: string | null = this.route.snapshot.queryParamMap.get('token');
    const error: string | null = this.route.snapshot.queryParamMap.get('error');

    if (token) {
      this.authService.saveToken(token);
      this.userApiService.getCurrentUser().subscribe(
        data => {
          this.login(data);
        }, err => {
          this.errorMessage = err.error.message;
        }
      );
    } else if (error) {
      this.errorMessage = error;
    }
  }

  login(user: any): void {
    this.authService.saveUser(user);
    this.currentUser = this.authService.getUser();
  }

  onLogin(): void {
    document.location.href = this.discordURL;
  }
}
