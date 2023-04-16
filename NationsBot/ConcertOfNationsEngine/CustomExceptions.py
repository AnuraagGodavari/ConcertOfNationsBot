from logger import *

class CustomException(Exception):
    """Parent class of any custom exception. Used to identify if an exception is any of the below classes."""
    pass


class NonFatalError(CustomException):
    """ Something went wrong that otherwise has no description and which shouldn't kill the program."""
    def __init__(self, args):
        super().__init__(args)
        logInfo(str(args[0]), stackLevel = 1)

class InputError(CustomException):
    """Something went wrong with the inputs to this function, either that they weren't parsed correctly or are invalid."""

    def __init__(self, args):
        super().__init__(args)
        logInfo(f"Input Error: \"{str(args)}\"", stackLevel = 1)

class LogicError(CustomException):
    """Something went wrong in the program logic."""
    def __init__(self, args):
        super().__init__(args)
        logInfo(f"Logic Error: \"{str(args)}\"", stackLevel = 1)