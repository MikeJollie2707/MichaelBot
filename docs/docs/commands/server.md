# Settings commands

These are commands that focus in providing Quality of Life for the guild. It comes with logging, welcoming, bad words filtering (new), goodbye (new), reaction roles (new), enabling/disabling a command (new).

## \_\_init\_\_ [INTERNAL]

*This section is labeled as [INTERNAL], meaning that is is **NOT** a command. It is here only to serve the developers purpose.*

A constructor of the category. This set the `Core` category's emoji as `🛠`.

## log_enable

Enable logging in your server.

**Full Signature:**

```py
@commands.command(aliases = ["log-enable"])
@commands.has_guild_permissions(manage_guild = True)
@commands.bot_has_permissions(send_messages = True)
@commands.bot_has_guild_permissions(view_audit_log = True)
@commands.cooldown(rate = 1,  per = 3.0, type = commands.BucketType.guild)
async def log_enable(self, ctx):
```
