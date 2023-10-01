from copy import copy
import collections
from math import *

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
        manpower (int): The amount of this population's size that has mobilized as manpower
    """

    def __init__(self, size, growthrate, occupation, identifiers, manpower = 0):
        self.size = size
        self.growthrate = round(growthrate, 5)
        self.occupation = occupation
        self.identifiers = identifiers
        self.manpower = manpower

    def grow_population(self, compound):
        """
        Change the population size based on the growth rate
        """

        self.size = floor(self.size * ((1 + self.growthrate) ** compound))

    def apply_modifiers(self, all_modifiers, remove_modifiers = False):
        """
        Iterate through a list of modifiers, applying all those that apply.
        """

        multiplier = 1

        if remove_modifiers:
            multiplier = -1

        for modifier in all_modifiers:

            #Continue if the modifier's prerequisite occupation or identifiers are different from this population's.
            if ("Occupation" in modifier.keys()):
                if (modifier["Occupation"] != self.occupation): continue

            if ("Identifiers" in modifier.keys()):
                identifiers_set = set(self.identifiers.values())
                if not(identifiers_set.issuperset(modifier["Identifiers"])): continue

            if ("Growth" in modifier.keys()):
                self.growthrate += modifier["Growth"] * multiplier
                self.growthrate = round(self.growthrate, 5)