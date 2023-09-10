from common import *
from logger import *

import pprint
from random import *
from copy import deepcopy
import re

from GameUtils import filehandling, mapping

from ConcertOfNationsEngine.gamehandling import *
from ConcertOfNationsEngine.gameobjects import *

import ConcertOfNationsEngine.territories as territories
import ConcertOfNationsEngine.buildings as buildings
import ConcertOfNationsEngine.populations as populations


valid_statuspatterns = ["Enemy$", "None$"]

# Validations

def validate_relation(newrelation):
        
    if (not(newrelation) or newrelation == "None"):
        return True
    
    for statuspattern in valid_statuspatterns:

        if (re.search(statuspattern, newrelation, flags=re.ASCII)):
            return True

    return False

# Set diplomatic relations

def set_relation(relation, *nations):

    nationNames = [nation.name for nation in nations]

    for i in range(len(nations)):
        nation = nations[i]
        for nationName in nationNames[:i] + nationNames[i+1:]:
            nation.diplomacy[nationName] = relation

            if not(relation): nation.diplomacy.pop(nationName)
