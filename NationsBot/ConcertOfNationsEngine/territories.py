import math
from copy import copy

from database import *
from logger import *
import imgur

from GameUtils import operations as ops
from GameUtils import filehandling

import ConcertOfNationsEngine.gamehandling as gamehandling
from ConcertOfNationsEngine.concertofnations_exceptions import *

import ConcertOfNationsEngine.dateoperations as dates

import ConcertOfNationsEngine.buildings as buildings


#Building operations

def hasbuilding(nation, territoryName, buildingName):

    territoryInfo = nation.get_territory(territoryName)

    return bool(buildingName in territoryInfo["Buildings"])

def newbuildingstatus(nation, territoryName, buildingName, newstatus, savegame):

    if (not hasbuilding(nation, territoryName, buildingName)):
        return False

    territoryInfo = nation.get_territory(territoryName)

    if (buildingName not in territoryInfo["Buildings"]):
        return False

    logInfo(f"Territory {territoryName} changing building {buildingName} status from {territoryInfo['Buildings'][buildingName]}")

    if buildings.validate_status(newstatus):

        oldstatus = territoryInfo["Buildings"][buildingName]

        territoryInfo["Buildings"][buildingName] = newstatus

        #Change whether or not the building's effects are active

        if (oldstatus != "Active" and newstatus == "Active"): 
            nation.add_buildingeffects(buildings.get_alleffects(buildingName, savegame), territoryInfo)

        elif (oldstatus == "Active" and newstatus != "Active"): 
            nation.remove_buildingeffects(buildings.get_alleffects(buildingName, savegame), territoryInfo)

        #Change nation bureaucratic load based on if the building is under construction or not

        blueprint = buildings.get_blueprint(buildingName, savegame)

        if (oldstatus.startswith("Constructing:") and not newstatus.startswith("Constructing:")):
            
            if ("Bureaucratic Cost" in blueprint.keys()): 
                for category, val in blueprint["Bureaucratic Cost"].items(): nation.bureaucracy[category] = (nation.bureaucracy[category][0] - val, nation.bureaucracy[category][1])

        elif (newstatus.startswith("Constructing:") and not oldstatus.startswith("Constructing:")):
            
            if ("Bureaucratic Cost" in blueprint.keys()): 
                for category, val in blueprint["Bureaucratic Cost"].items(): nation.bureaucracy[category] = (nation.bureaucracy[category][0] + val, nation.bureaucracy[category][1])

    logInfo(f"New building status: {territoryInfo['Buildings'][buildingName]}")

    return territoryInfo['Buildings'][buildingName]

def togglebuilding(nation, territoryName, buildingName, savegame):

    if (not hasbuilding(nation, territoryName, buildingName)):
        return False

    territoryInfo = nation.get_territory(territoryName)

    logInfo(f"Territory {territoryName} toggling building {buildingName} with current status {territoryInfo['Buildings'][buildingName]}")

    # Switch between Active and Inactive if the building is one or the other

    if (territoryInfo["Buildings"][buildingName] == "Active"):
        territoryInfo["Buildings"][buildingName] = "Inactive"
        nation.remove_buildingeffects(buildings.get_alleffects(buildingName, savegame), territoryInfo)

    elif (territoryInfo["Buildings"][buildingName] == "Inactive"):
        territoryInfo["Buildings"][buildingName] = "Active"
        nation.add_buildingeffects(buildings.get_alleffects(buildingName, savegame), territoryInfo)

    logInfo(f"New building status: {territoryInfo['Buildings'][buildingName]}")

    return territoryInfo['Buildings'][buildingName]

def destroybuilding(nation, territoryName, buildingName):

    if (not hasbuilding(nation, territoryName, buildingName)):
        return False

    territoryInfo = nation.get_territory(territoryName)

    territoryInfo["Buildings"].pop(buildingName)

    logInfo(f"Territory {territoryName} destroyed building {buildingName}")


# Effects

def add_buildingeffects(territoryInfo, effects, remove_modifiers = False):
    """
    Add the local territory-specific effects of a building
    """

    if ("Population" in effects.keys()):
        apply_population_modifiers(territoryInfo, effects["Population"], remove_modifiers)
    

#Manpower management

def get_manpower(nation, territoryName):

    return nation.get_territory(territoryName)["Manpower"]

def recruit_manpower(nation, territoryName, recruitment_amt):
    """ Recruit manpower for this territory proportionally from among the population """

    territoryInfo = nation.get_territory(territoryName)

    total_pop = sum([pop.size for pop in territoryInfo["Population"]])

    pop_shares = [pop.size/total_pop for pop in territoryInfo["Population"]]

    for i, pop in enumerate(territoryInfo["Population"]):

        pop.manpower += round(pop_shares[i] * recruitment_amt)

    territoryInfo["Manpower"] += recruitment_amt

def disband_manpower(nation, territoryName, disband_amt):
    """ Reduce the available manpower of this territory and distribute it proportionally among the population """

    territoryInfo = nation.get_territory(territoryName)

    #Account for manpower edited in manually
    real_manpower = sum([pop.manpower for pop in territoryInfo["Population"]])

    pop_shares = [pop.manpower/(real_manpower or 1) for pop in territoryInfo["Population"]]

    for i, pop in enumerate(territoryInfo["Population"]):

        pop_disbandamt = round(pop_shares[i] * disband_amt)

        if (pop_disbandamt > pop.manpower): pop_disbandamt = pop.manpower

        pop.manpower -= pop_disbandamt

    territoryInfo["Manpower"] -= disband_amt


#Population management

def get_totalpopulation(nation, territoryName):
    """ Returns True if the sum of the populations in this territory is greater than 0, otherwise returns False """

    return sum([pop.size for pop in nation.get_territory(territoryName)["Population"]])

def add_population(nation, territoryName, population):
    nation.territories[territoryName]["Population"].append(population)

    return population

def get_population(nation, territoryName, occupation, identifiers):
    """ Returns a population in this territory matching specified occupation and identifiers or False if none exists """

    territory_info = nation.get_territory(territoryName)

    pop = next(
        (
            pop for pop in territory_info["Population"] 
            if pop.occupation == occupation
            and identifiers == pop.identifiers
        ), False)

    return pop

def remove_population(nation, territoryName, occupation, identifiers):
    
    pop = get_population(nation, territoryName, occupation, identifiers)

    territory_info = nation.get_territory(territoryName)

    pop = next(
        (
            pop for pop in territory_info["Population"] 
            if pop.occupation == occupation
            and identifiers == pop.identifiers
        ), 
        False
        )

    if (pop): territory_info["Population"].remove(pop)

    return pop

def grow_all_populations(territoryInfo, compound):
    """
    Grow the territory's population

    Args:
        compound (int): Exponent applied to 1 + the population growth rate
    """

    for pop in territoryInfo["Population"]:
        pop.grow_population(compound)

def apply_population_modifiers(territoryInfo, all_modifiers, remove_modifiers = False):
    """
    Apply relevant modifiers to all populations in this territory
    """

    logInfo("all_modifiers", details = all_modifiers)

    for pop in territoryInfo["Population"]:
        pop.apply_modifiers(all_modifiers, remove_modifiers)

def change_population(nation, territoryName, newsize, occupation, identifiers):
    """ Changes the size of a population in this territory matching specified occupation and identifiers or False if none exists """
    
    pop = get_population(nation, territoryName, occupation, identifiers)

    if not(pop):
        return False

    pop.size = newsize

    return pop

def change_populationgrowth(nation, territoryName, growthrate, occupation, identifiers):
    """ Changes the size of a population in this territory matching specified occupation and identifiers or False if none exists """
    
    pop = get_population(nation, territoryName, occupation, identifiers)

    if not(pop):
        return False

    pop.growthrate = growthrate

    return pop

#New turn operations    

def newturnresources(territoryInfo, savegame):

    buildingsIncome = buildings.get_territories_buildingincome(territoryInfo, savegame)
            
    totalrevenue = ops.combineDicts(buildingsIncome)
    return totalrevenue

def advanceconstruction(territoryInfo, savegame, bureaucracy):
    """
    Enable all buildings that have completed construction by current savegame date
    """

    neweffects = []

    logInfo(f"Advancing construction for buildings in {territoryInfo['Name']}")

    for building, oldstatus in territoryInfo["Savegame"]["Buildings"].items():

        if ("Constructing" not in oldstatus):
            continue

        if (dates.date_grtrThan_EqlTo(savegame.date, dates.date_fromstr(oldstatus.split(':')[-1]))):
            territoryInfo["Savegame"]["Buildings"][building] = "Active"

            for category, cost in buildings.get_blueprint(building, savegame)["Bureaucratic Cost"].items():
                bureaucracy[category] = (bureaucracy[category][0] - cost, bureaucracy[category][1])

            logInfo(f"{building} now active from date {oldstatus.split(':')[-1]}")

            neweffects.append(buildings.get_alleffects(building, savegame))

    return ops.combineDicts(*neweffects)