import re


def bound(lowerBound, val, upperBound):
    return max(lowerBound, min(upperBound, val))

def sort(list):
    for i in range(len(list)):
        minimum = i
        
        for j in range(i + 1, len(list)):
            if list[j] < list[minimum]:
                minimum = j
                
        list[minimum], list[i] = list[i], list[minimum]
    
    return list
    
def isSufficient(num1, num2 = 1, threshold = 1):
    if num1 > threshold:
        return num1
    else:
        return num2

def isWithin(num1, num2 = 1, threshold = 1):
    if num1 < threshold:
        return num1
    else:
        return num2

def combineDicts(*args):
    rtnDict = {}
    for arg in args:
        if arg == None:
            continue

        for key in arg.keys():
            if key in rtnDict.keys():
                if isinstance(rtnDict[key], dict):
                    rtnDict[key] = combineDicts(rtnDict[key], arg[key])
                else:
                    try: rtnDict[key] += arg[key]
                    except: pass
            else:
                rtnDict[key] = arg[key]

    return rtnDict

def isInt(inStr: str):
     return bool(re.search("^-?[1234567890]*$", inStr))

def isPositiveInt(inStr: str):
     return bool(re.search("^0*?[123456789]+0*$", inStr))

def isNonnegativeInt(inStr: str):
     return bool(re.search("^[1234567890]*$", inStr))

def isFloat(inStr: str):
     return bool(re.search("^-?[1234567890]*(\.[1234567890]*)?$", inStr))

def isNonnegativeFloat(inStr: str):
     return bool(re.search("^[1234567890]*(\.[1234567890])?$", inStr))