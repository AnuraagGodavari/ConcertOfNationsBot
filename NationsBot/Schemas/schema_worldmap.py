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

def validate_territory_pos(pos, path):
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

def validate_territory_edges(edges, path):
    pass

def validate_territory_details(input_json, path):
    pass

def validate_territory_resources(input_json, path):
    pass


schema_worldmap = {
    "name": schema.SchemaProperties(primitive_type = str.__name__),
    "territories":
    [
        {
            "name": schema.SchemaProperties(primitive_type = str.__name__),
            "id": schema.SchemaProperties(primitive_type = int.__name__),
            "pos": schema.SchemaProperties(validator = validate_territory_pos),
            "edges": schema.SchemaProperties(validator = validate_territory_edges),
            "details": schema.SchemaProperties(validator = validate_territory_details),
            "resources": schema.SchemaProperties(validator = validate_territory_resources)
        }
    ]
}