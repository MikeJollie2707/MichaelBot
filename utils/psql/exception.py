__all__ = (
    "Error",
    "GetError",
    "InsertError",
    "DeleteError",
    "UpdateError",
    "DuplicateArrayElement",
)

class Error(Exception):
    '''A base error for high-level PostgreSQL operations.'''

class GetError(Error):
    '''A base error for SELECT operations.
    
    Notes
    -----
    This should only be raised when `get_x()` is implicitly called.
    This will NOT be raised if the user explicitly calls `get_x()`.
    '''

class InsertError(Error):
    '''A base error for INSERT operations.'''

class DeleteError(Error):
    '''A base error for DELETE operations.'''

class UpdateError(Error):
    '''A base error for UPDATE operations.'''

class DuplicateArrayElement(UpdateError):
    '''Raised when trying to add an element that's already available in a unique-only list (set).'''
