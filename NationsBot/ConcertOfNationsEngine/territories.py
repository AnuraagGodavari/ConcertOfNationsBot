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

def hasbuilding(nation, terrID, buildingName):

    territoryInfo = nation.get_territory(terrID)

    return bool(buildingName in territoryInfo["Buildings"])

def add_building(nation, terrID, buildingName, status, blueprint):

    territory = nation.get_territory(terrID)

    if (not hasbuilding(nation, terrID, buildingName)):
        territory["Buildings"][buildingName] = list()

    #Add Node Costs
    if ("Node Costs" in blueprint):
        node_costs = blueprint["Node Costs"]
        for k, v in node_costs.items(): territory["Nodes"][k] = (territory["Nodes"][k][0] + v, territory["Nodes"][k][1])

    nation.territories[terrID]["Buildings"][buildingName].append(status) 

def newbuildingstatus(nation, terrID, buildingName, buildingIndex, newstatus, savegame):

    if (not hasbuilding(nation, terrID, buildingName)):
        return False

    territoryInfo = nation.get_territory(terrID)

    if (buildingName not in territoryInfo["Buildings"]):
        return False

    logInfo(f"Territory {terrID} changing building {buildingName} {buildingIndex} status from {territoryInfo['Buildings'][buildingName]}")

    if buildings.validate_status(newstatus):

        oldstatus = territoryInfo["Buildings"][buildingName][buildingIndex]

        territoryInfo["Buildings"][buildingName][buildingIndex] = newstatus

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

    logInfo(f"New building status: {territoryInfo['Buildings'][buildingName][buildingIndex]}")

    return territoryInfo['Buildings'][buildingName][buildingIndex]

def togglebuilding(nation, terrID, buildingName, buildingIndex, savegame):

    if (not hasbuilding(nation, terrID, buildingName)):
        return False

    territoryInfo = nation.get_territory(terrID)

    logInfo(f"Territory {terrID} toggling building {buildingName} {buildingIndex} with current status {territoryInfo['Buildings'][buildingName]}")

    # Switch between Active and Inactive if the building is one or the other

    if (territoryInfo["Buildings"][buildingName][buildingIndex] == "Active"):
        territoryInfo["Buildings"][buildingName][buildingIndex] = "Inactive"
        nation.remove_buildingeffects(buildings.get_alleffects(buildingName, savegame), territoryInfo)

    elif (territoryInfo["Buildings"][buildingName][buildingIndex] == "Inactive"):
        territoryInfo["Buildings"][buildingName][buildingIndex] = "Active"
        nation.add_buildingeffects(buildings.get_alleffects(buildingName, savegame), territoryInfo)

    logInfo(f"New building status: {territoryInfo['Buildings'][buildingName][buildingIndex]}")

    return territoryInfo['Buildings'][buildingName][buildingIndex]

def destroybuilding(nation, terrID, buildingName, buildingIndex, blueprint):

    if (not hasbuilding(nation, terrID, buildingName)):
        return False

    territoryInfo = nation.get_territory(terrID)

    territoryInfo["Buildings"][buildingName].pop(buildingIndex)

    if (len(territoryInfo["Buildings"][buildingName]) < 1):
         territoryInfo["Buildings"].pop(buildingName)

    #Remove Node Costs
    if ("Node Costs" in blueprint):
        node_costs = blueprint["Node Costs"]
        for k, v in node_costs.items(): territoryInfo["Nodes"][k] = (territoryInfo["Nodes"][k][0] - v, territoryInfo["Nodes"][k][1])

    logInfo(f"Territory {terrID} destroyed building {buildingName} {buildingIndex}")

def validate_building_requirements(terrID, nation, savegame):
    """ Check if all buildings in this territory have what they need to remain active """

    territoryInfo = nation.territories[terrID]

    for buildingName in territoryInfo["Buildings"].keys():

        if (territoryInfo["Buildings"][buildingName] != "Active"):
            continue

        blueprint = buildings.get_blueprint(buildingName, savegame)
        
        if not ("Prerequisites" in blueprint.keys()):
            continue

        if not(nation.validate_prerequisites(blueprint["Prerequisites"], terrID, only_active = True)):
            territoryInfo["Buildings"][buildingName] = "Inactive"


# Effects

def add_buildingeffects(territoryInfo, effects, remove_modifiers = False):
    """
    Add the local territory-specific effects of a building
    """

    if ("Population" in effects.keys()):
        apply_population_modifiers(territoryInfo, effects["Population"], remove_modifiers)
    

#Manpower management

def get_manpower(nation, terrID):

    return nation.get_territory(terrID)["Manpower"]

def recruit_manpower(nation, terrID, recruitment_amt):
    """ Recruit manpower for this territory proportionally from among the population """

    territoryInfo = nation.get_territory(terrID)

    total_pop = sum([pop.size for pop in territoryInfo["Population"]])

    pop_shares = [pop.size/total_pop for pop in territoryInfo["Population"]]

    for i, pop in enumerate(territoryInfo["Population"]):

        pop.manpower += round(pop_shares[i] * recruitment_amt)

    territoryInfo["Manpower"] += recruitment_amt

def disband_manpower(nation, terrID, disband_amt):
    """ Reduce the available manpower of this territory and distribute it proportionally among the population """

    territoryInfo = nation.get_territory(terrID)

    #Account for manpower edited in manually
    real_manpower = sum([pop.manpower for pop in territoryInfo["Population"]])

    pop_shares = [pop.manpower/(real_manpower or 1) for pop in territoryInfo["Population"]]

    for i, pop in enumerate(territoryInfo["Population"]):

        pop_disbandamt = round(pop_shares[i] * disband_amt)

        if (pop_disbandamt > pop.manpower): pop_disbandamt = pop.manpower

        pop.manpower -= pop_disbandamt

    territoryInfo["Manpower"] -= disband_amt


#Population management

def get_totalpopulation(nation, terrID):
    """ Returns True if the sum of the populations in this territory is greater than 0, otherwise returns False """

    return sum([pop.size for pop in nation.get_territory(terrID)["Population"]])

def add_population(nation, terrID, population):
    nation.territories[terrID]["Population"].append(population)

    return population

def get_population(nation, terrID, occupation, identifiers):
    """ Returns a population in this territory matching specified occupation and identifiers or False if none exists """

    territory_info = nation.get_territory(terrID)

    pop = next(
        (
            pop for pop in territory_info["Population"] 
            if pop.occupation == occupation
            and identifiers == pop.identifiers
        ), False)

    return pop

def remove_population(nation, terrID, occupation, identifiers):
    
    pop = get_population(nation, terrID, occupation, identifiers)

    territory_info = nation.get_territory(terrID)

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

    for pop in territoryInfo["Population"]:
        pop.apply_modifiers(all_modifiers, remove_modifiers)

def change_population(nation, terrID, newsize, occupation, identifiers):
    """ Changes the size of a population in this territory matching specified occupation and identifiers or False if none exists """
    
    pop = get_population(nation, terrID, occupation, identifiers)

    if not(pop):
        return False

    pop.size = newsize

    return pop

def change_populationgrowth(nation, terrID, growthrate, occupation, identifiers):
    """ Changes the size of a population in this territory matching specified occupation and identifiers or False if none exists """
    
    pop = get_population(nation, terrID, occupation, identifiers)

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

    logInfo(f"Advancing construction for buildings in territory {territoryInfo['ID']}")

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