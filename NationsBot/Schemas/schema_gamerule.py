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

        if not (isinstance(amount, int)):
            raise InputError(f"{path}: Bureaucracy amounts must be numbers")


numval_dict_schemaproperties = schema.SchemaProperties(
    validator = schema.schema_validate_values, 
    schema = 
        schema.SchemaProperties(primitive_type = gamerule_numbertypes)
    )


schema_gamerule_building = {
    "Costs": schema.SchemaProperties(validator = validate_resources),
    
    "Bureaucratic Cost": schema.SchemaProperties(validator = validator_bureaucracy),
    
    "Node Costs": schema.SchemaProperties(validator = validate_resources, is_required = False),

    "Effects":
    {
        "Nation":
        {
            "Bureaucracy": schema.SchemaProperties(validator = validator_bureaucracy),

            "National Modifiers":
            {
                "Tax": schema.SchemaProperties(primitive_type = gamerule_numbertypes)
            }
        },
        "Territory":
        {
        }
    },

    "Maintenance": schema.SchemaProperties(validator = validate_resources),

    "Mines": schema.SchemaProperties(validator = validate_resources),

    "Produces": schema.SchemaProperties(validator = validate_resources),

    "Construction Time": schema.SchemaProperties(primitive_type = int),

    "Territory Maximum": schema.SchemaProperties(validator = validate_positive_int, is_required = False)
}

schema_gamerule_unit = {
    "Costs": schema.SchemaProperties(validator = validate_resources),

    "Bureaucratic Cost": schema.SchemaProperties(validator = validator_bureaucracy),

    "Maintenance": schema.SchemaProperties(validator = validate_resources),

    "Construction Time": schema.SchemaProperties(primitive_type = int)
}

schema_gamerule = {
	
	"Resources": [schema.SchemaProperties(primitive_type = str)],
	
	"Terrain Data": numval_dict_schemaproperties,
	
	"Base Bureaucracy": numval_dict_schemaproperties,

	"Buildings": schema.SchemaProperties(validator = schema.schema_validate_values, schema = schema_gamerule_building),

	"Units": schema.SchemaProperties(validator = schema.schema_validate_values, schema = schema_gamerule_unit),

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