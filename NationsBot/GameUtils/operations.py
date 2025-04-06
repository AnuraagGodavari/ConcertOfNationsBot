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

def combineDicts(*args, subtractDicts = False):
    rtnDict = {}
    for arg in args:
        if arg == None:
            continue

        for key in arg.keys():
            if key in rtnDict.keys():
                if isinstance(rtnDict[key], dict):
                    rtnDict[key] = combineDicts(rtnDict[key], arg[key])
                else:
                    try: 
                        if not(subtractDicts): rtnDict[key] += arg[key]
                        else: rtnDict[key] -= arg[key]
                    except: pass
            else:
                rtnDict[key] = arg[key]

    return rtnDict

def invertValue(v):

    if isinstance(v, (int, float)):
        return v*-1
    elif isinstance(v, (dict)):
        return invertDict(v)
    elif (isinstance(v, list)):
        return invertList(v)
    else:
        return v

def invertList(l):

    invertedList = list()
    
    for i, v in enumerate(l):
        invertedList[i] = invertValue(v)

    return invertedList

def invertDict(d):

    invertedDict = dict()

    for k, v in d.items():
        invertedDict[k] = invertValue(v)

    return invertedDict

def isInt(inStr: str):
     return bool(re.search("^-?[1234567890]*$", inStr))

def isPositiveInt(inStr: str):
     return bool(re.search("^0*?[123456789]+[1234567890]*$", inStr))

def isNegativeInt(inStr: str):
     return bool(re.search("^-0*?[123456789]+[1234567890]*$", inStr))

def isNonnegativeInt(inStr: str):
     return bool(re.search("^[1234567890]*$", inStr))

def isFloat(inStr: str):
     return bool(re.search("^-?[1234567890]*(\.[1234567890]*)?$", inStr))

def isNonnegativeFloat(inStr: str):
     return bool(re.search("^[1234567890]*(\.[1234567890])?$", inStr))