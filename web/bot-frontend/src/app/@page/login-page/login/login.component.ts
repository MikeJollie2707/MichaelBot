import { Component, OnInit } from '@angular/core';
import {TokenService} from '../../../@service/security/token.service';
import {ActivatedRoute} from '@angular/router';
import {UserApiService} from '../../../@service/api/user-api.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {
  isLoggedIn = false;
  isLoginFailed = false;
  errorMessage = '';
  currentUser: any;
  githubURL = 'http://localhost:8080/oauth2/authorization/github?redirect_uri=http://localhost:4200';

  constructor(private tokenService: TokenService,
              private userApiService: UserApiService,
              private route: ActivatedRoute) {}

  ngOnInit(): void {
    const token: string | null = this.route.snapshot.queryParamMap.get('token');
    const error: string | null = this.route.snapshot.queryParamMap.get('error');
    if (this.tokenService.getToken()) {
      this.isLoggedIn = true;
      this.currentUser = this.tokenService.getUser();
    } else if (token) {
      this.tokenService.saveToken(token);
      this.userApiService.getCurrentUser().subscribe(
        data => {
          this.login(data);
        },
        err => {
          this.errorMessage = err.error.message;
          this.isLoginFailed = true;
        }
      );
    } else if (error) {
      this.errorMessage = error;
      this.isLoginFailed = true;
    }
  }

  login(user: any): void {
    this.tokenService.saveUser(user);
    this.isLoginFailed = false;
    this.isLoggedIn = true;
    this.currentUser = this.tokenService.getUser();
    window.location.reload();
  }
}
