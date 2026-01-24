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

gamerule_numbertypes = (int, float, complex)

def validate_positive_int(num, path, gamerule = None, **kwargs):
    """
    Some fields must be an int above 0.
    """

    if not (isinstance(num, int)):
        raise InputError(f"{path}: This number must be a positive integer.")

    if not (num > 0):
        raise InputError(f"{path}: This number must be a positive integer.")


def validate_resources(resources, path, gamerule = None, **kwargs):
    """
    Resources must be an object where the keys are resources that exist in the gamerule and the values are numbers.
    """

    if not (gamerule):
        return

    if not (isinstance(resources, dict)):
        raise InputError(f"{path}: Resources must be in a dictionary/json object.")

    for resource, amount in resources.items():

        if (resource not in gamerule["Resources"] + ["Money"]):
            raise InputError(f"{path}: Key {resource} in resources must be a resource which exists in the gamerule.")

        if not (isinstance(amount, (int, float, complex))):
            raise InputError(f"{path}: Resource amounts must be numbers")

def validator_bureaucracy(bureaucracy, path, gamerule = None, **kwargs):
    """
    Bureaucracy must be an object where the keys are bureaucratic categories that exist in the gamerule and the values are numbers.
    """

    if not (gamerule):
        raise InputError(f"{path}: There must be a gamerule provided in order to validate bureaucracy.")

    if not (isinstance(bureaucracy, dict)):
        raise InputError(f"{path}: Bureaucracy must be in a dictionary/json object.")

    for category, amount in bureaucracy.items():

        if (category not in gamerule["Base Bureaucracy"].keys()):
            raise InputError(f"{path}: Key {category} in bureaucracy must be a resource which exists in the gamerule.")

def validate_prerequisites_exist(prerequisites, path, gamerule = None, **kwargs):
    """
    A building's prerequisites must exist in the gamerule.
    """

    if not (gamerule):
        raise InputError(f"{path}: There must be a gamerule provided in order to validate prerequisites.")

    if not (isinstance(prerequisites, list)):
        raise InputError(f"{path}: Prerequisites must be in a list/array.")

    for prerequisite in prerequisites:

        if not (isinstance(prerequisite, str)):
            raise InputError(f"{path}: Prerequisite must be a string indicating building names.")

        if not (prerequisite in gamerule["Buildings"].keys()):
            raise InputError(f"{path}: Prerequisite {prerequisite} must be a building which exists in the gamerule.")


numval_dict_schemaproperties = schema.SchemaProperties(
    validator = schema.schema_validate_values, 
    schema = 
        schema.SchemaProperties(primitive_type = gamerule_numbertypes)
    )


schema_gamerule_building = {
    "Costs": schema.SchemaProperties(validator = validate_resources, is_required = False),
    
    "Bureaucratic Cost": schema.SchemaProperties(validator = validator_bureaucracy, is_required = False),
    
    "Node Costs": schema.SchemaProperties(validator = validate_resources, is_required = False),

    "Effects":
    {
        "Nation":
        {
            "Bureaucracy": schema.SchemaProperties(validator = validator_bureaucracy, is_required = False),

            "National Modifiers":
            {
                "Tax": schema.SchemaProperties(primitive_type = gamerule_numbertypes, is_required = False)
            }
        },

        "Territory":
        {
            "Nodes": schema.SchemaProperties(validator = validate_resources, is_required = False)
        }
    },

    "Maintenance": schema.SchemaProperties(validator = validate_resources, is_required = False),

    "Mines": schema.SchemaProperties(validator = validate_resources, is_required = False),

    "Produces": schema.SchemaProperties(validator = validate_resources, is_required = False),

    "Construction Time": schema.SchemaProperties(primitive_type = int),

    "Territory Maximum": schema.SchemaProperties(validator = validate_positive_int, is_required = False),

    "Prerequisites": {

        "Buildings": {

            "Nation": schema.SchemaProperties(validator = validate_prerequisites_exist, is_required = False),

            "Territory": schema.SchemaProperties(validator = validate_prerequisites_exist, is_required = False)

        }
    },

    "Tags": [

		schema.SchemaProperties(primitive_type = str, is_required = False)
    
    ]
}

schema_gamerule_unit = {
    "Costs": schema.SchemaProperties(validator = validate_resources),

    "Bureaucratic Cost": schema.SchemaProperties(validator = validator_bureaucracy),

    "Maintenance": schema.SchemaProperties(validator = validate_resources),

    "Construction Time": schema.SchemaProperties(primitive_type = int),

    "Prerequisites": {

        "Buildings": {

            "Nation": schema.SchemaProperties(validator = validate_prerequisites_exist, is_required = False),

            "Territory": schema.SchemaProperties(validator = validate_prerequisites_exist, is_required = False)

        }
    },

    "Speed": schema.SchemaProperties(primitive_type = int),

    "Tags": [

		schema.SchemaProperties(primitive_type = str, is_required = False)
    
    ]
}

schema_gamerule_vehicle = {

    **schema_gamerule_unit,

    "Carry Capacity": schema.SchemaProperties(primitive_type = int),

    "Crew": schema.SchemaProperties(primitive_type = int),

    "Costs": schema.SchemaProperties(validator = validate_resources)
}

schema_gamerule = {
	
	"Resources": [schema.SchemaProperties(primitive_type = str)],
	
	"Terrain Data": numval_dict_schemaproperties,
	
	"Base Bureaucracy": numval_dict_schemaproperties,

	"Buildings": schema.SchemaProperties(validator = schema.schema_validate_values, schema = schema_gamerule_building),

	"Units": schema.SchemaProperties(validator = schema.schema_validate_values, schema = schema_gamerule_unit),

	"Vehicles": schema.SchemaProperties(validator = schema.schema_validate_values, schema = schema_gamerule_vehicle),

	"Base Population Growth": schema.SchemaProperties(primitive_type = gamerule_numbertypes),

	"Base National Modifiers":
	{
		"Tax": schema.SchemaProperties(primitive_type = gamerule_numbertypes),
		"Manpower Cost": schema.SchemaProperties(primitive_type = gamerule_numbertypes)
	},

	"Occupations":
	[
		schema.SchemaProperties(primitive_type = str)
	],

	"Population Identifiers": schema.SchemaProperties(
        validator = schema.schema_validate_values, 
        schema = 
            [schema.SchemaProperties(primitive_type = str)]
        )
	
}