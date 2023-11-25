import json, os, inspect, pprint, copy

from GameUtils import filehandling
from ConcertOfNationsEngine.concertofnations_exceptions import *

from logger import *

class SchemaProperties:
    """
    Describes how a json object should be structured.

    Args:
        validator (function): A function used to validate objects of this schema
        primitive_type (str): The name of the type that this object should match
        is_required (bool): Describes if this object is expected to exist, wherever it is stored. 
    """

    def __init__(self, validator = None, primitive_type: str = None, is_required: bool = True):
        self.validator = validator
        self.primitive_type = primitive_type
        self.is_required = is_required

    def validate(self, input_obj, path, **kwargs):
        """
        Validate a value in a json object defined by this SchemaProperties instance.

        Args:
            input_obj: The object to validate
            path: Where in the total schema we are looking
            **kwargs: Optional keyword args that may be used by a dedicated validator function.
        """

        logInfo(f"Validating Schema Path: {path}")
        
        if self.validator:
            self.validator(input_obj, path, **kwargs)
        
        elif self.primitive_type:
            
            if type(input_obj).__name__!= self.primitive_type:
                raise InputError(f"{path}: Must be type: {self.primitive_type}")


def schema_validate_list(schema, input_obj, path, **kwargs):
    """
    Validate a schema object of a list type

    Args:
        schema: The structure to compare against
        input_obj: The object to validate
        path: Where in the total schema we are looking
        **kwargs: Optional keyword args that may be used by a dedicated validator function.
    """

    logInfo(f"Validating Schema Path: {path}")

    for i, element in enumerate(input_obj):
        schema_validate(schema[0], element, path + f'[{i}]', **kwargs)

def schema_validate_dict(schema, input_obj, path, **kwargs):
    """
    Validate a schema dict/js object

    Args:
        schema: The structure to compare against
        input_obj: The object to validate
        path: Where in the total schema we are looking
        **kwargs: Optional keyword args that may be used by a dedicated validator function.
    """

    logInfo(f"Validating Schema Path: {path}")

    for key, val in schema.items():

        currpath = path + '.' + key

        if isinstance(val, SchemaProperties):

            if (val.is_required and key not in input_obj.keys()):
                raise InputError(f"{path}: Required key {key} not present in object")

            val.validate(input_obj[key], currpath, **kwargs)

        else:
            schema_validate(val, input_obj[key], currpath, **kwargs)

def schema_validate(schema, input_obj, path = 'schema', **kwargs):
    """
    Validate a schema object of any valid type

    Args:
        schema: The structure to compare against
        input_obj: The object to validate
        path: Where in the total schema we are looking
        **kwargs: Optional keyword args that may be used by a dedicated validator function.
    """

    logInfo(f"Validating Schema Path: {path}")

    if isinstance(schema, SchemaProperties):
        schema.validate(input_obj, path, **kwargs)

    elif isinstance(schema, list):
        schema_validate_list(schema, input_obj, path, **kwargs)

    elif isinstance(schema, dict):
        schema_validate_dict(schema, input_obj, path, **kwargs)

    else:
        raise InputError(f"{path}: A schema object's value must either be a dict/json object, a list or a SchemaProperties instance.")
        

