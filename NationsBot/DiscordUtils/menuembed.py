from math import *
import re

import discord

from common import *
from logger import *

from ConcertOfNationsEngine.concertofnations_exceptions import *

""" A dictionary of depth 1 where keys are player IDs and values are menu objects """
menucache = dict()

class PaginationView(discord.ui.View):

    def __init__(self, parentmenu, page):
        super().__init__()
        self.parentmenu = parentmenu
        self.page = page

    @discord.ui.button(label="Previous Page", style=discord.ButtonStyle.green)
    async def previous_page(self, interaction, button):
        
        if (interaction.user.id != self.parentmenu.userid):
            return
        
        await interaction.response.edit_message(
            embed = self.parentmenu.toEmbed(self.page - 1), 
            view = self.parentmenu.embedView(self.page - 1)
        )

    @discord.ui.button(label="Next Page", style=discord.ButtonStyle.green)
    async def next_page(self, interaction, button):
        
        if (interaction.user.id != self.parentmenu.userid):
            return
        
        await interaction.response.edit_message(
            embed = self.parentmenu.toEmbed(self.page + 1), 
            view = self.parentmenu.embedView(self.page + 1)
        )


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

    def __init__(self, title, description, userid, imgfile = None, imgurl = None, sortable = False, fields = None, isPaged = False, pagesize = 25, format_text = True):
        self.title = title
        self.description = description
        self.userid = userid
        self.imgfile = imgfile
        self.imgurl = imgurl
        self.sortable = sortable
        self.fields = fields or list()
        self.isPaged = isPaged
        self.pagesize = max(1, min(pagesize, 25))
        self.format_text = format_text

    def adjust_pagenumber(self, pagenumber):
        """ Adjust page number so it is between 0 and the last possible page number before overflow """
        return max(0, min(pagenumber, floor(len(self.fields) / self.pagesize)))

    def sortContent(self, *keys):

        if not (self.sortable):
            return False

        if len(keys) > 2: keys = keys[0:2]                
        
        if len(keys) < 1: raise InputError("Not enough sorting keys")
        
        #If there is only one sorting key, we sort on that key within the field
        if (len(keys) == 1):
            sortlambda = lambda field: field[1][keys[0]] if keys[0] in field[1].keys() else 0

        #If there are two sorting keys, we sort on the value of key1 within a dict at field[key0]
        else:
            sortlambda = lambda field: field[1][keys[0]][keys[1]] if keys[1] in field[1][keys[0]].keys() else 0

        try:
            self.fields.sort(key = sortlambda)
        except Exception as e:
            logError(e)
            raise InputError(f"Invalid sorting keys: {keys}") 

    def toEmbed(self, pagenumber = 0, *sortkeys):
        
        pagenumber = self.adjust_pagenumber(pagenumber)

        embed = discord.Embed(
                title = f"{self.title}" + (f" Page {pagenumber + 1}" * self.isPaged),
                description = self.description
            )

        if (self.imgurl): embed.set_image(url = self.imgurl)

        pagestart = pagenumber * self.pagesize
        pageend = min(len(self.fields), (pagenumber + 1) * self.pagesize)
        
        paginatedFields = self.fields[pagestart:pageend]

        for field in paginatedFields:

            title = field[0]
            content = ""

            if (type(field[1]) == dict):

                contentDict = field[1]
                
                for key in contentDict.keys():
                    
                    if key == '__class__': continue
                    if key == '__module__': continue

                    '''
                    if type(contentDict[key]) == dict: continue

                    if type(contentDict[key]) == list:
                        if type(contentDict[key][0]) == dict:
                            continue
                    '''

                    contentstr = json.dumps(contentDict[key], indent=2)

                    #Regex: Get rid of JSON object brackets, whitespace or comma-only lines, and quotes.
                    contentstr = re.sub(r'[{}\[\]]', '', contentstr)
                    contentstr = re.sub(r'\s+,?\n', '\n', contentstr)
                    contentstr = re.sub(r'"', '', contentstr)

                    if (contentstr):
                        content += f"{key}: {contentstr}\n"
                    

            else:
                content = str(field[1])

            content = str(content)
            if self.format_text: content = f"`{content}`"

            embed.add_field(
                name = title,
                value = content
            )

        return embed

    def embedView(self, pagenumber = 0):
        
        if not (self.isPaged):
            return None

        pagenumber = self.adjust_pagenumber(pagenumber)

        return PaginationView(self, pagenumber)


def assignMenu(playerid, menu):
    menucache[str(playerid)] = menu

def getMenu(playerid):
    
    if not(str(playerid) in menucache.keys()):
        return False

    return menucache[str(playerid)]