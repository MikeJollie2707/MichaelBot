import {Injectable} from '@angular/core';
import {BehaviorSubject} from 'rxjs';

const TOKEN_KEY = 'auth-token';
const USER_KEY = 'auth-user';

@Injectable({providedIn: 'root'})
export class AuthService {
  isAuthChanged: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(!!sessionStorage.getItem(TOKEN_KEY));

  signOut(): void {
    sessionStorage.clear();
    this.isAuthChanged.next(!!sessionStorage.getItem(TOKEN_KEY));
  }

  public saveToken(token: string): void {
    window.sessionStorage.removeItem(TOKEN_KEY);
    window.sessionStorage.setItem(TOKEN_KEY, token);
    this.isAuthChanged.next(!!sessionStorage.getItem(TOKEN_KEY));
  }

  public saveUser(user: any): void {
    window.sessionStorage.removeItem(USER_KEY);
    window.sessionStorage.setItem(USER_KEY, JSON.stringify(user));
    this.isAuthChanged.next(!!sessionStorage.getItem(TOKEN_KEY));
  }

  public getToken(): string {
    return (sessionStorage.getItem(TOKEN_KEY) as string);
  }

  public getUser(): any {
    return JSON.parse(sessionStorage.getItem(USER_KEY) as string);
  }
}
