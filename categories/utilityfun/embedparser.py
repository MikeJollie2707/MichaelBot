import discord

import datetime

ATTRS = [
    "TITLE",
    "DESCRIPTION",
    "URL",
    "TIMESTAMP",
    "COLOR",
    "FOOTER",
    "IMAGE",
    "THUMBNAIL",
    "VIDEO",
    "PROVIDER",
    "AUTHOR",
    "FIELDS"
]

class InvalidDiscordSyntax(Exception):
    pass

class InvalidEmbedSyntax(Exception):
    pass

class CustomEmbed:
    def __init__(self):
        self.embed = {}
    
    def TITLE_attr(self, title):
        if isinstance(title, str):
            self.embed["title"] = title
        else:
            raise TypeError("'title' must be 'str'")
    
    def DESCRIPTION_attr(self, description):
        if isinstance(description, str):
            self.embed["description"] = description
        else:
            raise TypeError("'description' must be 'str'")

    def COLOR_attr(self, color):
        try:
            color = int(color)
        except ValueError:
            raise TypeError("'color' must be 'int'")
        
        self.embed["color"] = color
    
    def AUTHOR_attr(self, author_info):
        keywords = [
            "NAME",
            "ICON_URL"
        ]
        author = {}

        args = author_info.split()
        i = 0
        params = ""
        command = ""
        while (i < len(args)):
            if (args[i] in keywords):
                command = args[i]
                i += 1
            else:
                while ((i < len(args)) and (args[i] not in keywords)):
                    params += args[i] + " "
                    i += 1
                
                params = params[:-1] # Remove the last space
                if command == "NAME":
                    if params != "":
                        author["name"] = params
                    else:
                        pass # Raise exception here
                if command == "ICON_URL":
                    if params != "":
                        author["icon_url"] = params
                    else:
                        pass # Raise exception here
        
        if len(author) != 0:
            self.embed["author"] = author
        else:
            pass # raise exception here
    
    def FIELDS_attr(self, fields_info):
        keywords = [
            "NAME",
            "VALUE",
            "INLINE"
        ]
        fields = []
        field = {}

        args = fields_info.split(" ")
        i = 0
        params = ""
        command = ""
        while (i < len(args)):
            if (args[i] in keywords):
                if (args[i] == "NAME"): # If there's a NAME attribute then a new embed has been created.    
                    field = {}
                command = args[i]
                i += 1
            else:
                while ((i < len(args)) and (args[i] not in keywords)):
                    params += args[i] + " "
                    i += 1
                
                params = params[:-1]
                if command == "NAME":
                    if params != "":
                        field["name"] = params
                    else:
                        pass # Raise exception here
                if command == "VALUE":
                    if params != "":
                        field["value"] = params
                    else:
                        pass # Raise exception here
                if command == "INLINE":
                    if params != "":
                        field["inline"] = bool(int(params))
                        if "name" not in field:
                            pass # Raise exception here
                        else:
                            fields.append(field)
                    else:
                        pass # Raise different exception
                
                if "name" not in field:
                    pass # Raise exception here
                
                params = ""
        
        self.embed["fields"] = fields
                



    

    
def parser(string):
    embed = CustomEmbed()
    args = string.split()
    i = 0
    params = ""
    command = ""
    while (i < len(args)):
        if (args[i] in ATTRS):
            command = args[i]
            i += 1
        else:
            while ((i < len(args)) and (args[i] not in ATTRS)):
                params += args[i] + " "
                i += 1
            
            params = params[:-1] # Remove the last space
            try:
                eval("%s.%s_attr(\"%s\")" % ("embed", command, params))
                params = ""
                command = ""
            except TypeError as te:
                print(te)
            except Exception as e:
                print(e)
    
    print(embed.embed)
    return embed.embed

    