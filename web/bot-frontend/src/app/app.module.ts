import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppComponent } from './app.component';
import { HomePageComponent } from './@page/home-page/home-page.component';
import { NavbarComponent } from './@shared/navbar/navbar.component';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import {HTTP_INTERCEPTORS, HttpClientModule} from '@angular/common/http';
import {ButtonModule} from 'primeng/button';
import {DividerModule} from 'primeng/divider';
import {AppRoutingModule} from './app-routing.module';
import {AuthInterceptor} from './@service/security/auth.interceptor';
import { LoginPageComponent } from './@page/login-page/login-page.component';
import {CardModule} from 'primeng/card';
import { LoginComponent } from './@page/login-page/login/login.component';
import {SidebarComponent} from './@shared/sidebar/sidebar.component';
import {MessageModule} from 'primeng/message';
import { ProfilePageComponent } from './@page/profile-page/profile-page.component';

@NgModule({
  declarations: [
    AppComponent,
    HomePageComponent,
    NavbarComponent,
    SidebarComponent,
    LoginPageComponent,
    LoginComponent,
    ProfilePageComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    HttpClientModule,
    ButtonModule,
    DividerModule,
    NgbModule, // ng bootstrap
    AppRoutingModule,
    CardModule,
    MessageModule,
  ],
  providers: [{provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true}],
  bootstrap: [AppComponent]
})
export class AppModule { }