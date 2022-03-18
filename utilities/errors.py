import lightbulb
import hikari

class CustomCacheDesync(hikari.HikariError):
    '''Exception raised when the bot's cache is desync from database.'''
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
