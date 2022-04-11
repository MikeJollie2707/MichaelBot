import lightbulb
import hikari

class CustomAPIFailed(hikari.HTTPError):
    '''Exception raised when a third-party API call failed (not status 200).'''
    pass

class CustomCheckFailed(lightbulb.CheckFailure):
    '''Exception raised when a custom check (not lightbulb check) failed.'''
    pass

class NoDatabase(CustomCheckFailed):
    '''Exception raised when the bot doesn't have a database.'''
    pass

class GuildDisabled(CustomCheckFailed):
    '''Exception raised when the guild disable the command.'''
    pass

class GuildBlacklisted(CustomCheckFailed):
    '''Exception raised when the guild is blacklisted by the bot's owner.'''
    pass

class UserBlacklisted(CustomCheckFailed):
    '''Exception raised when the user is blacklisted by the bot's owner.'''
    pass
