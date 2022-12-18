# Welcome to MichaelBot Documentation

Welcome to MichaelBot's documentation. This documents all the bot's commands along with its features.

- For general purposes, please refers to the `Commands` heading.
- For those who are interested in some of the more secret stuffs, feel free to look at the bot source code.

Below are some of the topics that are might not obvious from a user perspective.

## Prefix vs Slash

MichaelBot has 2 main types of command: prefix command and slash command. Prefix command is the OG "command system" that's been widely implemented for pretty much every single bot. Slash command is the official command system in Discord that's been implemented fairly recently. MichaelBot tries to balance these 2, but there are some pros and cons to them:

**Slash > Prefix:**

- Is officially supported by Discord and is super newbie-friendly.
- Can use Tab to autocomplete. This makes it somewhat unnecessary for the user to remember the arguments. This is excellent when the user need to input some sort of choice into the command.
- Arguments are generally easier to deal with since Discord do all the necessary text parsing.
- Prefix commands don't work without verifying the bot after reaching 100 servers. This is technically not the case for slash commands.

**Prefix > Slash:**

- Is familiar to a lot of people.
- Can alias commands. This allows users to smash commands super fast.
- Slash commands have a hard limit of 100 commands per bot. Prefix commands don't have such thing.
- Slash commands don't have hidden commands; all commands are public.
- Slash commands' parent can't be invoked (`queue` cannot be invoked if a subcommand `queue clear` is registered). This is not the case for prefix commands.

With these pros and cons, sometimes some commands are exclusive to slash or prefix only. This will be mentioned in each command entry. Besides slash commands, Discord also have *user commands* and *message commands*. However, the bot rarely uses them for important features, so you can safely ignore them for the most part.

By default, I'll recommend you to use the Prefix version of the command. However, in some cases, Slash command might performs the job easier. I'll sometimes put my preferences if that's the case.

## Cooldown

Some commands have cooldown. This is to ensure the bot has time to do things first before it is invoked again. This is quite common for commands that deal with heavy stuffs such as music or communicating with servers. Some cooldown are simply to avoid spamming potential.

Cooldown is applied to a certain target. There are 4 targets a cooldown can apply:

- A user. This means the user can't execute the command within an interval.
- A channel. This means the command can't be executed in the same channel within an interval.
- A guild. This means the command can't be executed in the same guild within an interval.
- Everywhere. This means the command can't be executed by anyone within an interval.

**Technical:** Most cooldown are soft; they can be reset by resetting the bot or use some commands to reset. Some cooldown are hard-coded; they're saved within the database and you might need to edit the table (and the cache) to remove it.

### Concurrency

Some commands also have a limited amount of time they can be active at a time. This is referred to as max concurrency, where the command will have a maximum of `n` active sessions. This is common for commands that stays active for more than a few seconds. Usually, the bot will limit to 1 per target (target is same as the target in cooldown).

For example, the command `barter` is a command with a session to listen for any inputs from the user. Therefore, it has a max concurrency of 1 per user. This means the same user can't invoke `barter` again until the command is finished (and any cooldown).

## Parameters

Many commands require parameters to be passed in. Although the `help` command already provide a good amount of info, it is still limited because it is auto-generated. Note that these are mostly applied to Prefix Commands; Slash Commands is super user-friendly so you might not even need to care about most of these stuffs.

Take the command signature `foo <bar> [bar2 = bla] [bar3 = 1] [*baz = None]`

- All parameters are separated by space. Which means if you invoke `foo 1 2 3`, it'll store as `bar = 1, bar2 = 2, bar3 = 3` and not `bar = 1 2 3`.
- `<parameter>` means this parameter is required. That means `bar` is a required parameter.
- `[parameter]` or `[parameter = None]` means this parameter is optional. That means `bar2`, `bar3`, and `baz` are optional parameters.
    - `parameter = sth` means the default value of a parameter is set to whatever `sth` is. This usually appears in optional parameters.
- `*parameter` means it'll consume all the remaining text. This means if you invoke `foo 1 2 3 4 5 6`, it'll store as `bar = 1, bar2 = 2, bar3 = 3, baz = 4 5 6`.

Slash Commands have none of the above problem since parameters are separated by Tab, and they also have indication which parameters are required.

### Parameter Type

There are several types the bot will work with. The most common one is plain text, followed by numbers. These are pretty straightforward. The less obvious types are such as a Discord User or a Discord Guild. There are several ways to pass in such types, which will be shown in this table.

| Type                             | Pass into Prefix Commands       | Pass into Slash Commands                                                              |
|----------------------------------|---------------------------------|---------------------------------------------------------------------------------------|
| Plain text                       | Literally any text you type.    | Literally any text you type.                                                          |
| Numbers                          | Literally any numbers you type. | Literally any numbers you type.                                                       |
| Discord User/Member/Channel/Role | ID > Mention > Name > Nickname  | Choose from the option (you might need to partially type the name for it to show up). |
| Discord Guild                    | ID                              | ID                                                                                    |
| Time                             | 1d10h10m10s or hh:mm:ss         | 1d10h10m10s or hh:mm:ss                                                               |
