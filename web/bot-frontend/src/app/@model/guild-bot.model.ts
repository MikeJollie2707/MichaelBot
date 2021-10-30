export class GuildBot {
  constructor(
    public name: string,
    public whitelist: boolean,
    public prefix: string,
    public enableLog: boolean,
    public logChannel: number,
    public enableWelcome: boolean,
    public welcomeChannel: number,
    public welcomeText: string,
    public id?: number,
  ) {}
}
