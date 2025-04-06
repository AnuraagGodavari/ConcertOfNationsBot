'''
All Trades Schema:

Trades:
{
    "Nation 1": {
        "Nation 2":
        {
            "Resource 1": 1
        }
    },    
    "Nation 2": {
        "Nation 1":
        {
            "Resource 2": 1
        }
    },
}
'''

'''
Offers Schema:

Offers: {
    "Offering Nation":
    {
        "Target Nation":{
        
            ...Trade
        
        }
    }
}

'''


def add_trade():
    pass

def modify_trade():
    
    #If trade does not exist, call add_trade
    
    pass

def remove_trade():
    pass

def calculate_trade(nation_name):
    pass