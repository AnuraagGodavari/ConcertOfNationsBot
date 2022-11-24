import json, datetime, pprint, traceback, inspect

from common import *

debugmodeOn = False
    
def log(level, message, details = None, stackLevel = 0):
    """
    Prints log information to the console and writes it to a log file.
    
    Args:
        level (string): Descriptor of the log level. Might be DEBUG, WARNING, ERROR etc.
        details (dict): information like traceback, context etc.
        stackLevel(int): Log the name of the function this far up the stack from the function that's logging
    """
    
    #Should refer to the function 1 level up the stack which called log
    stackLevel += 1

    logtime = datetime.datetime.now()

    # = "<Function> Line <Lineno>"
    callerFunctionInfo = f"{inspect.stack()[stackLevel].filename.split('/')[-1].split('.')[0]}.{inspect.stack()[stackLevel].function}() Line {inspect.stack()[stackLevel].lineno}"
    
    #Print info
    print(f"{level}: [{logtime} {callerFunctionInfo}] {message}")
    if (details): pprint.pprint(details)
    
    #Write to file
    with open(masterlog, 'a') as log:

        if (details == None):
            log.write(f"{level}: [{logtime} {callerFunctionInfo}] {message}\n\n")
        
        elif (type(details is dict)):
            log.write(f"{level}: [{logtime} {callerFunctionInfo}] {message}\n[{logtime}] Additional Info: {json.dumps(details, indent=4)}\n")
            
        else:
            log.write(f"{level}: [{logtime} {callerFunctionInfo}] {message}\n[{logtime}] Additional Info: {details}\n")


def logInitial(message):
    
    with open(masterlog, 'a') as logfile: logfile.write("\n\n")
        
    log("START", message)

    
def logInfo(message, details = None, stackLevel = 0):
    """
    Logs an error by writing the error's name, traceback and other details to the master log
    
    Args:
        details(dict): Additional data about the log or the message
        stackLevel(int): Log the name of the function this far up the stack from the function that's logging
    """

    #Should refer to the function 1 level up the stack which called logInfo
    stackLevel += 1
    
    #Log the message and user-provided details
    log("INFO", message, details, stackLevel)
    
    #Add further information to the errorData and return
    
    logtime = {
        "message": message,
        "details": details,
        "time": str(datetime.datetime.now())
    }
            
    return logtime
    
    
def logError(error, errorInfo = None, stackLevel = 0):
    """
    Logs an error by writing the error's name, traceback and other details to the master log
    
    Args:
        error (Exception): The exception object itself
        errorInfo (dict): Additional metadata about the error
        stackLevel(int): Log the name of the function this far up the stack from the function that's logging
    """

    #Should refer to the function 1 level up the stack which called logError
    stackLevel += 1
    
    #Log the error, stack trace and context details
    
    errorData = { "Stack Trace": traceback.format_exception(type(error), error, error.__traceback__) }
    if (errorInfo): errorData["Context"] = errorInfo
    
    log("ERROR", str(error), errorData, stackLevel)
    
    #Add further information to the errorData and return
    
    errorTime = str(datetime.datetime.now())
    errorData["Error Time"] = errorTime
    errorData["Exception"] = str(error)
            
    return errorData