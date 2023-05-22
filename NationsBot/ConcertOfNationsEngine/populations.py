from copy import copy
import collections

from database import *
from logger import *
import imgur

from GameUtils import operations as ops
from GameUtils import filehandling

import ConcertOfNationsEngine.gamehandling as gamehandling
from ConcertOfNationsEngine.concertofnations_exceptions import *

def identifiers_list_toDict(gamerule, *identifiers):
    return {
        category: identifier
        for category, identifiers_list in gamerule["Population Identifiers"].items() for identifier in identifiers_list 
        if identifier in identifiers
    }

def validate_population(gamerule, size, occupation, identifiers, growth = 0):
    
    #Validate size
    if (type(size) == int):
        if size < 0:
            raise InputError(f"Invalid size {size}, must be a non-negative integer")
    elif (type(size) == str):
        if not(ops.isNonnegativeInt(size)):
            raise InputError(f"Invalid size {size}, must be a positive integer")
    else:
        raise InputError(f"Invalid size {size}, must be a positive integer")
    
    #Validate growth rate
    if (type(growth) == str):
        if not(ops.isFloat(growth)):
            raise InputError(f"Invalid growth rate {growth}, must be a decimal value")
    elif(type(growth) not in (float, int)):
        raise InputError(f"Invalid growth rate {growth}, must be a decimal value")

    #Validate occupation
    if not(occupation in gamerule["Occupations"]):
        raise InputError(f"Unknown occupation {occupation}") 

    if not(gamerule["Population Identifiers"].keys() == identifiers.keys()):
        raise InputError(f"Must have the following identifiers: {' '.join(list(gamerule['Population Identifiers'].keys()))}")

    for category, identifier in identifiers.items():
        if not (identifier in gamerule["Population Identifiers"][category]):
            raise InputError(f"Invalid {category} identifier \"{identifier}\"")

    return True
    

class Population:
    """
    Represents a group of people sharing certain identifiers and an occupation.

    Args:
        size (int): The number of people in this population category.
        growth (float): The growth rate of this population per turn
        occupation (string): The job that all of these people share.
        identifiers (dict): A dict with string values, each value representing an identifying characteristic of this population.
    """

    def __init__(self, size, growth_modifier, occupation, identifiers):
        self.size = size
        self.growth_modifier = growth_modifier
        self.occupation = occupation
        self.identifiers = identifiers