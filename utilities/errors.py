import lightbulb
import hikari

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
