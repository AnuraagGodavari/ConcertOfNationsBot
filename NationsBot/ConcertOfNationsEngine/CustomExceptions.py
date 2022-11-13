from logger import *

class NonFatalError(Exception):
    
    def __init__(self, args):
        super().__init__(args)
        logInfo(str(args[0]))

class InputError(Exception):
    
    def __init__(self, args):
        super().__init__(args)
        logInfo(f"Input Error: \"{str(args)}\"")

class GameError(Exception):
    
    def __init__(self, args):
        super().__init__(args)
        logInfo(f"Game Error: \"{str(args)}\"")