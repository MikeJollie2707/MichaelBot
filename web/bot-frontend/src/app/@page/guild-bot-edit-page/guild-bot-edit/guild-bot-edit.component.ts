import {Component, OnInit, ViewChild} from '@angular/core';
import {ActivatedRoute} from '@angular/router';
import {GuildBotApiService} from '../../../@service/api/guild-bot-api.service';
import {GuildBot} from '../../../@model/guild-bot.model';
import {Guild} from '../../../@model/guild.model';
import {Channel} from '../../../@model/channel.model';
import {MessageService} from 'primeng/api';

@Component({
  selector: 'app-guild-bot-edit',
  templateUrl: './guild-bot-edit.component.html',
  styleUrls: ['./guild-bot-edit.component.scss'],
  providers: [MessageService]
})
export class GuildBotEditComponent implements OnInit {
  guildBot: GuildBot | undefined;
  guildBotId = '';

  // edit attr
  enableLog = false;
  enableWelcome = false;

  // channels that bot can send message to
  channels: Channel[];
  selectedLogChannel: Channel;
  selectedWelcomeChannel: Channel;

  @ViewChild('f') form: any;

  constructor(private route: ActivatedRoute,
              private guildBotApi: GuildBotApiService,
              private messageService: MessageService) {}

  ngOnInit(): void {
    const routeParams = this.route.snapshot.paramMap;
    this.guildBotId = routeParams.get('guildBotId');
    const guild: Guild = this.findGuild(this.guildBotId);
    if (guild) {
      this.channels = guild.channels;
    }
    this.guildBotApi.getGuildBot(this.guildBotId).subscribe((data) => {
      this.guildBot = data;
      if (this.guildBot) {
        this.enableLog = this.guildBot.enableLog;
        this.enableWelcome = this.guildBot.enableWelcome;
      }
    });
  }

  findGuild(guildBotId: string): Guild {
    const guilds: Guild[] = JSON.parse(sessionStorage.getItem('guilds'));
    for (const g of guilds) {
      if (g.id === guildBotId) { return g; }
    }
    return null;
  }

  onSubmit(): void {
    if (this.form.valid) {
      console.log('form: ' + JSON.stringify(this.form.value));
      this.messageService.add({key: 'bc', severity: 'success', summary: 'Saved', detail: 'content saved successfully'});
    }
  }

}
