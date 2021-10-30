import {RouterModule, Routes} from '@angular/router';
import {NgModule} from '@angular/core';
import {HomePageComponent} from './@page/home-page/home-page.component';
import {LoginPageComponent} from './@page/login-page/login-page.component';
import {ProfilePageComponent} from './@page/profile-page/profile-page.component';
import {GuildBotEditPageComponent} from './@page/guild-bot-edit-page/guild-bot-edit-page.component';

const routes: Routes = [
  {path: 'home', component: HomePageComponent},
  {path: 'login', component: LoginPageComponent},
  {path: 'profile', component: ProfilePageComponent},
  {path: 'profile/guild-bot-edit/:guildBotId', component: GuildBotEditPageComponent},
  {path: '', redirectTo: '/home', pathMatch: 'full'},
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule],
})
export class AppRoutingModule {}
