import { Component, OnInit } from '@angular/core';
import {ActivatedRoute} from '@angular/router';
import {GuildBotApiService} from '../../../@service/api/guild-bot-api.service';
import {GuildBot} from '../../../@model/guild-bot.model';

@Component({
  selector: 'app-guild-bot-edit',
  templateUrl: './guild-bot-edit.component.html',
  styleUrls: ['./guild-bot-edit.component.scss']
})
export class GuildBotEditComponent implements OnInit {
  guildBot: GuildBot | undefined;
  guildBotId = '';

  // edit attr
  enableLog = false;
  enableWelcome = false;

  constructor(private route: ActivatedRoute,
              private guildBotApi: GuildBotApiService) {}

  ngOnInit(): void {
    const routeParams = this.route.snapshot.paramMap;
    this.guildBotId = routeParams.get('guildBotId');
    this.guildBotApi.getGuildBot(this.guildBotId).subscribe((data) => {
      this.guildBot = data;
      if (this.guildBot) {
        this.enableLog = this.guildBot.enableLog;
        this.enableWelcome = this.guildBot.enableWelcome;
      }
    });
  }

}
