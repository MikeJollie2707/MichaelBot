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
# This contains all possible attributes in all options. DON'T USE THIS in parser().
KEYS = [
    "NAME",
    "VALUE",
    "INLINE",
    "ICON_URL"
]

class InvalidDiscordSyntax(SyntaxError):
    '''
    This exception is raised when the syntax for the embed is not correct by the Discord API standard.
    '''
    pass

class InvalidEmbedSyntax(SyntaxError):
    '''
    This exception is raised when the syntax for the embed is not correct by the parser itself.
    '''
    pass

class CustomEmbed:
    def __init__(self):
        self.embed = {}
    
    def TITLE_attr(self, title):
        self.embed["title"] = title
    
    def DESCRIPTION_attr(self, description):
        self.embed["description"] = description
    
    def URL_attr(self, url):
        self.embed["url"] = url

    def TIMESTAMP_attr(self, timestamp_confirm):
        try:
            if int(timestamp_confirm) == 1:
                self.embed["timestamp"] = datetime.datetime.utcnow()
        except ValueError:
            raise InvalidEmbedSyntax("`TIMESTAMP` must be 1 or 0.")

    def COLOR_attr(self, color):
        try:
            color = int(color, base = 16)
        except ValueError:
            raise InvalidEmbedSyntax("`COLOR` must be in hex numbers.")
        
        self.embed["color"] = color
    
    def FOOTER_attr(self, footer_info):
        pass

    def IMAGE_attr(self, image):
        pass

    def THUMBNAIL_attr(self, thumbnail):
        keywords = [
            "URL",
            "PROXY_URL",
            "HEIGHT",
            "WEIGHT"
        ]
        thumbnail = {}

        args = thumbnail.split()
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



    def VIDEO_attr(self, video):
        pass

    def PROVIDER_attr(self, provider_info):
        pass

    def AUTHOR_attr(self, author_info):
        keywords = [
            "NAME",
            "ICON_URL"
        ]
        keycount = {
            "NAME" : 0,
            "ICON_URL" : 0
        }
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
                    if keycount["NAME"] == 0:
                        if params != "":
                            author["name"] = params
                        else:
                            raise InvalidDiscordSyntax("`NAME` attribute in `AUTHOR` is required")

                        keycount["NAME"] = 1
                    else:
                        raise InvalidDiscordSyntax("`NAME` can only be mentioned once.")
                if command == "ICON_URL":
                    if params != "":
                        author["icon_url"] = params
                    else:
                        raise InvalidEmbedSyntax("Must specify `ICON_URL` in `AUTHOR` if mentioned")
        
        if len(author) != 0:
            self.embed["author"] = author
        else:
            raise InvalidEmbedSyntax("`AUTHOR` has wrong syntax. Must specify attribute `NAME`")
    
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
                        raise InvalidDiscordSyntax("`NAME` attribute in `FIELDS` is required.")
                if command == "VALUE":
                    if params != "":
                        field["value"] = params
                    else:
                        raise InvalidDiscordSyntax("`VALUE` attribute in `FIELDS` is required.")
                if command == "INLINE":
                    if params != "":
                        field["inline"] = bool(int(params))
                        if "name" not in field:
                            raise InvalidDiscordSyntax("`NAME` attribute in `FIELDS` is required.")
                        else:
                            fields.append(field)
                    else:
                        raise InvalidEmbedSyntax("`INLINE` attribute in `FIELDS` is required.")
                
                if "name" not in field:
                    raise InvalidDiscordSyntax("`NAME` attribute in `FIELDS` is required.")
                
                params = ""
        
        self.embed["fields"] = fields



    

    
def parser(string):
    '''
    Parse the input string and convert it to a dictionary that represents a Discord Embed object.

    Return type: `dict`
    '''

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

    