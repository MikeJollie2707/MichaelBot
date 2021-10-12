import { Component, OnInit } from '@angular/core';
import {AuthService} from '../../../@service/security/auth.service';
import {User} from '../../../@model/user.model';
import {Guild} from '../../../@model/guild.model';

@Component({
  selector: 'app-profile',
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss']
})
export class ProfileComponent implements OnInit {
  user?: User;
  managedGuilds: Guild[] = [];

  constructor(private authService: AuthService) { }

  ngOnInit(): void {
    this.user = this.authService.getUser() as User;
    this.filterManageGuild();
  }

  filterManageGuild(): void {
    // @ts-ignore
    this.managedGuilds = this.user.guilds.filter((guild) => guild.owner
      || guild.permissions === 'MANAGE_GUILD' || guild.permissions === 'ADMINISTRATOR');
  }

}
