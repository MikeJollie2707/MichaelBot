'''Contains funny text manipulations.'''

import random

__REPLACE_WORDS = {
    "small": "smol",
    "cute": "kawaii~",
    "love": "luv",
    "stupid": "baka",
    "what": "nani",
    "meow": "nya~"
}

__RANDOM_EMOTES = [
    " rawr x3",
    " OwO",
    " UwU",
    " o.O",
    " -.-",
    " >w<",
    " (⑅˘꒳˘)",
    " (ꈍᴗꈍ)",
    " (˘ω˘)",
    " (U ᵕ U❁)",
    " σωσ",
    " òωó",
    " (///ˬ///✿)",
    " (U ﹏ U)",
    " ( ͡o ω ͡o )",
    " ʘwʘ",
    " :3",
    " XD",
    " nyaa~~",
    " mya",
    " >_<",
    " 😳",
    " 🥺",
    " 😳😳😳",
    " rawr",
    " ^^",
    " ^^;;",
    " (ˆ ﻌ ˆ)♡ ",
    " ^•ﻌ•^ ",
    " /(^•ω•^)",
    " (✿oωo)"
]

__RANDOM_ACTIONS = [
    " *huggles tightly*",
    " *blushes*",
    " *twerks*",
    " *notices bulge*",
    " *screeches*",
    " *sweats*",
    " *whispers to self*",
]

def uwuify(text: str, /, *, allow_nyvowels = True, stutter_chance: float = 0.20, emote_chance: float = 0.8, action_chance: float = 0.05) -> str:
    '''
    Transfrom a text into uwu text.

    Parameters:
    - `text`: The text to transform.
    - `allow_nyvowels`: Whether or not to transform `na`, `no`, etc. into `nya`, `nyo`, etc.
    - `stutter_chance`: The chance to stutter a word. Must be `[0, 1]`.
    - `emote_chance`: The chance to put an emote after a punctuation like `,` or `.` Must be `[0, 1]`.
    - `action_chance`: The chance to put an action string after a word. Must be `[0, 1]`.
    '''
    words = text.split()

    for index, word in enumerate(words):
        words[index] = words[index].replace('l', 'w')
        words[index] = words[index].replace('L', 'W')
        words[index] = words[index].replace('r', 'w')
        words[index] = words[index].replace('R', 'W')
        
        if allow_nyvowels:
            words[index] = words[index].replace("na", "nya")
            words[index] = words[index].replace("Na", "Nya")
            words[index] = words[index].replace("NA", "NyA")

            words[index] = words[index].replace("ne", "nye")
            words[index] = words[index].replace("Ne", "Nye")
            words[index] = words[index].replace("NE", "NyE")

            words[index] = words[index].replace("no", "nyo")
            words[index] = words[index].replace("No", "Nyo")
            words[index] = words[index].replace("NO", "NyO")

            words[index] = words[index].replace("nu", "yu")
            words[index] = words[index].replace("Nu", "Nyu")
            words[index] = words[index].replace("NU", "NyU")

        if word in __REPLACE_WORDS:
            words[index] = __REPLACE_WORDS[word]
        
        is_stutter = random.random()
        if is_stutter <= stutter_chance:
            words[index] = f"{words[index][0]}-{words[index]}"
        
        is_emote = random.random()
        if is_emote <= emote_chance and words[index].endswith(('.', '?', '!', ',')):
            words[index] += random.choice(__RANDOM_EMOTES)
        
        is_action = random.random()
        if is_action <= action_chance:
            words[index] += random.choice(__RANDOM_ACTIONS)
    
    return ' '.join(words)

def pekofy(text: str) -> str:
    '''
    Simple implementation of pekofy by just adding `peko` after each sentences.
    '''

    words = text.split()
    for index, word in enumerate(words):
        for punc in ['.', '!', '?']:
            if word.endswith(punc):
                words[index] = words[index][:-1] + f" peko{punc}"
        
        if word == words[-1]:
            words[index] += " peko"
    
    return ' '.join(words)
