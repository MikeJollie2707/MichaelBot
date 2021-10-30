import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Observable} from 'rxjs';

@Injectable({providedIn: 'root'})
export class GuildBotApiService {
  constructor(private http: HttpClient) {}

  getGuildBot(guildBotId: string): Observable<any> {
    return this.http.get(`http://localhost:8080/api/guildBot/${guildBotId}`);
  }
}
