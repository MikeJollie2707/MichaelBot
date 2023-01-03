'''Custom exceptions (errors) to handle in global error handler.'''

import hikari
import lightbulb


class CustomAPIFailed(hikari.HTTPError):
    '''Exception raised when a third-party API call failed (not status 200).'''

class CustomCheckFailed(lightbulb.CheckFailure):
    '''Exception raised when a custom check (not lightbulb check) failed.'''

class NoDatabase(CustomCheckFailed):
    '''Exception raised when the bot doesn't have a database connection pool.'''

class NoHTTPClient(CustomCheckFailed):
    '''Exception raised when the bot doesn't have a http client.'''

class GuildDisabled(CustomCheckFailed):
    '''Exception raised when the guild disable the command.'''

class GuildBlacklisted(CustomCheckFailed):
    '''Exception raised when the guild is blacklisted by the bot's owner.'''

class UserBlacklisted(CustomCheckFailed):
    '''Exception raised when the user is blacklisted by the bot's owner.'''
