import {Guild} from './guild.model';

export class User {
  constructor(
    public id: string,
    public displayName: string,
    public email: string,
    public roles: string,
    public guilds: Guild[]
  ) {}
}
