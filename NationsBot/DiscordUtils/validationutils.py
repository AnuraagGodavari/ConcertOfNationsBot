from GameUtils import operations as ops

from ConcertOfNationsEngine.concertofnations_exceptions import *

def get_resources_input(args, savegame):

    if len(args) < 1:
        raise InputError("Not enough args!")

    elif (len(args) % 2 != 0):
        raise InputError("Odd number of args")

    resources_toadd = {args[n*2]: args[(n*2)+1] for n in range(int(len(args)/2))}

    for k, v in resources_toadd.items():
        
        if not(k in savegame.getGamerule()["Resources"] + ["Money"]):
            raise InputError(f"\"{k}\" is not a resource")

        if not (ops.isInt(v)):
            raise InputError(f"\"{v}\" is not a valid amount of resources")

        else:
            resources_toadd[k] = int(v)

    return resources_toadd