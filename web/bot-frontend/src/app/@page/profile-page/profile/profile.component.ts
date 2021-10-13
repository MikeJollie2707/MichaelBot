import { Component, OnInit } from '@angular/core';
import {AuthService} from '../../../@service/security/auth.service';
import {User} from '../../../@model/user.model';
import {Guild} from '../../../@model/guild.model';
import {Constant} from '../../../@shared/app.constant';

@Component({
  selector: 'app-profile',
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss']
})
export class ProfileComponent implements OnInit {
  user?: User;
  guilds: Guild[] = [];

  constructor(private authService: AuthService) { }

  ngOnInit(): void {
    this.user = this.authService.getUser() as User;
    this.filterManageGuild();
  }

  filterManageGuild(): void {
    // @ts-ignore
    this.guilds = this.user.guilds
      .filter((guild: Guild) =>
      guild.owner || guild.permissions === 'MANAGE_GUILD' || guild.permissions === 'ADMINISTRATOR'
    ).map((guild: Guild) => {
      if (guild.icon != null) {
        const newGuild = {...guild};
        newGuild.icon = Constant.DISCORD_BASE_IMG + 'icons/' + guild.id + '/' + guild.icon + '.png';
        return newGuild;
      } else {
        return guild;
      }
    });
  }

}
