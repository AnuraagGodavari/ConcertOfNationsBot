from logger import *

class CustomException(Exception):
    pass


class NonFatalError(CustomException):
    
    def __init__(self, args):
        super().__init__(args)
        logInfo(str(args[0]))

class InputError(CustomException):
    
    def __init__(self, args):
        super().__init__(args)
        logInfo(f"Input Error: \"{str(args)}\"")

class GameError(CustomException):
    
    def __init__(self, args):
        super().__init__(args)
        logInfo(f"Game Error: \"{str(args)}\"")