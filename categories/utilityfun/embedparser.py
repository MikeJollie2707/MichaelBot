import discord

ATTRS = [
    "TITLE",
    "DESCRIPTION",
    "COLOR",
    "AUTHOR",
    "THUMBNAIL",
    "FIELD"
]

class CustomEmbed:
    def __init__(self):
        self.title = ""
        self.description = ""
        self.color = 0x000000
        self.author = None
        self.thumbnail = None
        self.fields = []

        self.__embedlen__ = 0
    
    def title_attr(title):
        self.title = title
        self.__embedlen__ += len(title)
    
    def description_attr(description):
        self.description = description
        self.__embedlen__ += len(description)

    def color_attr(color):
        self.color = color
    
def parser(string):
    args = string.split()
    i = 0
    while (i < len(args)):
        params = []
        while (args[i] not in ATTRS):

            i += 1
        
        i += 1