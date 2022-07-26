import json, datetime, pprint, traceback

from common import *

debugmodeOn = False
	
def log(level, message, details = None):
	"""
	Prints log information to the console and writes it to a log file.
	
	Args:
		level (string): Descriptor of the log level. Might be DEBUG, WARNING, ERROR etc.
		details (dict): information like traceback, context etc.
	"""
	
	logtime = datetime.datetime.now()
	
	#Print info
	print(f"[{logtime}] {level}: {message}")
	if (details): pprint.pprint(details)
	
	#Write to file
	with open(masterlog, 'a') as log:
		
		if (details == None):
			log.write(f"[{logtime}] {level}: {message}\n\n")
		
		elif (type(details is dict)):
			log.write(f"[{logtime}] {level}: {message}\n[{logtime}] Additional Info: {json.dumps(details, indent=4)}\n")
			
		else:
			log.write(f"[{logtime}] {level}: {message}\n[{logtime}] Additional Info: {details}\n")


def logInitial(message):
	
	with open(masterlog, 'a') as logfile: logfile.write("\n\n")
		
	log("START", message)

	
def logInfo(message, details = None):
	"""
	Logs an error by writing the error's name, traceback and other details to the master log
	
	Args:
		error (Exception): The exception object itself
		serverID (int): The discord ID of the server where the command was executed
		authorID (int): The discord ID of the user who used the command that triggered the error.
	"""
	
	#Log the message and user-provided details
	log("INFO", message, details)
	
	#Add further information to the errorData and return
	
	logtime = {
		"message": message,
		"details": details,
		"time": str(datetime.datetime.now())
	}
			
	return logtime
	
	
def logError(error, errorInfo):
	"""
	Logs an error by writing the error's name, traceback and other details to the master log
	
	Args:
		error (Exception): The exception object itself
		serverID (int): The discord ID of the server where the command was executed
		authorID (int): The discord ID of the user who used the command that triggered the error.
	"""
	
	#Log the error, stack trace and context details
	
	errorData = { "Stack Trace": traceback.format_exception(type(error), error, error.__traceback__) }
	if (errorInfo): errorData["Context"] = errorInfo
	
	log("ERROR", str(error), errorData)
	
	#Add further information to the errorData and return
	
	errorTime = str(datetime.datetime.now())
	errorData["Error Time"] = errorTime
	errorData["Exception"] = str(error)
			
	return errorData