import json, datetime, pprint, traceback

from common import *

debugmodeOn = False
	
def log(level, message, info = None):
	"""
	Prints log information to the console and writes it to a log file.
	
	Args:
		level (string): Descriptor of the log level. Might be DEBUG, WARNING, ERROR etc.
		info (dict): information like traceback, context etc.
	"""
	
	logtime = datetime.datetime.now()
	
	with open(masterlog, 'a') as log:
		log.write(f"[{logtime}] {level}: {message}\n")
		
		if (info): 
			log.write(f"[{logtime}] Additional Info:")
			
			if (type(info) is dict):
				log.write(f"{json.dumps(info, indent=4)} \n")
				
			else:
				log.write(f"{info} \n")
				
		log.write("\n")
	
def log_error(error, errorInfo):
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