import discord

from common import *
from logger import *

from ConcertOfNationsEngine.CustomExceptions import *

""" A dictionary of depth 1 where keys are player IDs and values are menu objects """
menucache = dict()

class MenuEmbed:
    """
    An object that can create a discord embed with pages of fields.

    Attributes:
        title (str): Header for each embed
        description (str): Subheader/description for each embed
        sortable (bool): Is the content within this embed sortable?
        fields (list): list of tuples with the following format:
            [
                ...
                (
                    Title (str),
                    {
                        #Dictionary of depth <= 2, each key represents a line of text under title.
                        #Each key begins the line, values fill out the rest.
                    }
                )
                ...
            ]
    """

    def __init__(self, title, description, imgfile = None, imgurl = None, sortable = False, fields = None, pagesize = 25):
        self.title = title
        self.description = description
        self.imgfile = imgfile
        self.imgurl = imgurl
        self.sortable = sortable
        self.fields = fields
        self.pagesize = max(1, min(pagesize, 25))

    def sortContent(self, *keys):
        pass

    def toEmbed(self, pagenumber = 0, *sortkeys):

        embed = discord.Embed(
                title = f"{self.title} Page {pagenumber + 1}",
                description = self.description
            )

        if (self.imgurl): embed.set_image(url = self.imgurl)

        pagestart = min(len(self.fields) - self.pagesize, pagenumber * self.pagesize)
        pageend = min(len(self.fields), (pagenumber + 1) * self.pagesize)
        
        paginatedFields = self.fields[pagestart:pageend]

        for field in paginatedFields:

            title = field[0]
            contentDict = field[1]
            content = ""
            
            for key in contentDict.keys():
                
                if key == '__class__': continue
                if key == '__module__': continue

                if type(contentDict[key]) == dict: continue

                if type(contentDict[key]) == list:
                    if type(contentDict[key][0]) == dict:
                        continue

                content += f"{key}: {contentDict[key]}\n"


            embed.add_field(
                name = title,
                value = content
            )

        return embed

def assignMenu(playerid, menu):
    menucache[str(playerid)] = menu

def getMenu(playerid):
    return menucache[str(playerid)]