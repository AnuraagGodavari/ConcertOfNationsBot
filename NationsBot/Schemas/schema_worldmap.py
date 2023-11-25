import pprint
from math import *
from copy import copy

from database import *
from logger import *
import imgur

from GameUtils import operations as ops
import GameUtils.filehandling as filehandling
import GameUtils.schema as schema

import ConcertOfNationsEngine.gamehandling as gamehandling
from ConcertOfNationsEngine.concertofnations_exceptions import *

import ConcertOfNationsEngine.dateoperations as dates

import ConcertOfNationsEngine.buildings as buildings
import ConcertOfNationsEngine.territories as territories
import ConcertOfNationsEngine.populations as populations
import ConcertOfNationsEngine.military as military
import ConcertOfNationsEngine.diplomacy as diplomacy


# Territory validations

def validate_territory_pos(pos, path, **kwargs):
    """
    Territory positions must be a list of two numbers, like so: [x,y]
    """
    
    pos_format = "[x,y]"

    if (type(pos) not in (list, tuple)):
        raise InputError(f"{path}: Territory position must be formatted like: {pos_format}")

    elif (len(pos) != 2):
        raise InputError(f"{path}: Territory position must be formatted like: {pos_format}")

    for coord in pos:
        if not(isinstance(coord, (int, float, complex))):
            raise InputError(f"{path}: Coordinates must be numbers")

def validate_territory_edges(edges, path, worldmap = None, **kwargs):
    """
    Territory edges must be an object where the keys are territory ids and the values are distances to those territories.
    """

    if not (isinstance(edges, dict)):
        raise InputError(f"{path}: A territory's edges must be in a dictionary/json object.")

    all_territories = [territory["id"] for territory in worldmap["territories"]]

    for neighbor, dist in edges.items():

        if (int(neighbor) not in all_territories):
            raise InputError(f"{path}: Key {neighbor} in edges must be a string of a number equal to another territory's id.")

        if not (isinstance(dist, (int, float, complex))):
            raise InputError(f"{path}: Edges must be numbers")

def validate_territory_resources(resources, path, gamerule = None, **kwargs):
    """
    Territory resources must be an object where the keys are resources that exist in the gamerule and the values are numbers.
    """

    if not (gamerule):
        raise InputError(f"{path}: There must be a gamerule provided in order to validate territory resources.")

    if not (isinstance(resources, dict)):
        raise InputError(f"{path}: A territory's resources must be in a dictionary/json object.")

    for resource, amount in resources.items():

        if (resource not in gamerule["Resources"]):
            raise InputError(f"{path}: Key {resource} in resources must be a resource which exists in the gamerule.")

        if not (isinstance(amount, (int, float, complex))):
            raise InputError(f"{path}: Resource amounts must be numbers")


# Territory details validations

def validate_terrain(terrain, path, gamerule = None, **kwargs):
    """
    Territory details terrain must be a string in Gamerule["Terrain Data"].
    """

    if not (gamerule):
        raise InputError(f"{path}: There must be a gamerule provided in order to validate territory resources.")

    if not (isinstance(terrain, str)):
        raise InputError(f"{path}: A territory's terrain must be a string.")

    if (terrain not in gamerule["Terrain Data"]):
        raise InputError(f"{path}: Key {terrain} in terrain must be a terrain type which exists in the gamerule.")


schema_worldmap = {
    "name": schema.SchemaProperties(primitive_type = str.__name__),
    "territories":
    [
        {
            "name": schema.SchemaProperties(primitive_type = str.__name__),
            "id": schema.SchemaProperties(primitive_type = int.__name__),
            "pos": schema.SchemaProperties(validator = validate_territory_pos),
            "edges": schema.SchemaProperties(validator = validate_territory_edges),
            "details": {
                "Terrain": schema.SchemaProperties(validator = validate_terrain)
            },
            "resources": schema.SchemaProperties(validator = validate_territory_resources)
        }
    ]
}