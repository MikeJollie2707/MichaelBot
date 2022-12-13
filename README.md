# MichaelBot

## What's this?

This is a utility Discord Bot written in Python using `hikari`, `hikari-lightbulb`, and other libraries. This bot exists because I think it's a fun project.

The bot existed before using `discord.py`, but the library discontinued (and it resumes 3 days after I push the change onto this repository...), so I'm working on rewriting the entire thing with `hikari`. Many important features will be missing in the mean time.

## Features

- Basic Information
- Fun Commands
- Utility Commands
- Report and Suggest Features
- Music
- Economy Commands

More features will be added as I work on to restore the bot to its glory.

## Limitations

- Expect a lot of bugs.
- Uptime not 100% 24/7.

## Libraries

These are the libraries I used. All of these can be installed with `requirement.txt`. If you're on Windows, use `win_requirement.txt` instead (`uvloop` is not available on Windows). Note that I don't actively maintain on Windows, so if there are any troubles relating to version with `win_requirement.txt`, create an issue and I'll try to update it.

- [hikari](https://github.com/hikari-py/hikari)
    - [hikari-lightbulb](https://github.com/tandemdude/hikari-lightbulb)
    - [hikari-miru](https://github.com/HyperGH/hikari-miru)
- [Lavalink](https://github.com/freyacodes/Lavalink)
    - [lavaplayer](https://github.com/HazemMeqdad/lavaplayer)
- [asyncpg](https://github.com/MagicStack/asyncpg)
- [emoji](https://github.com/carpedm20/emoji/)
- [humanize](https://github.com/jmoiron/humanize)
- [psutil](https://github.com/giampaolo/psutil)
- [pytimeparse](https://github.com/wroberts/pytimeparse)
- [py_expression_eval](https://github.com/axiacore/py-expression-eval)
- [uvloop](https://github.com/MagicStack/uvloop)
- [mkdocs](https://github.com/mkdocs/mkdocs)
    - [mkdocs-material](https://github.com/squidfunk/mkdocs-material)
    - [mkdocstrings](https://github.com/mkdocstrings/mkdocstrings)
    - [mkdocstrings-python](https://github.com/mkdocstrings/python)
- [pip-autoremove](https://github.com/invl/pip-autoremove)

Build instructions available [here](./docs/docs/INSTALLATION.md).

## License

This project is under the [MIT LICENSE](LICENSE).

## Resources

These are the resources I used for the bot.

- [hikari Documentation](https://docs.hikari-py.dev/en/stable/) (a bit hard to follow)
- [lightbulb Documentation](https://hikari-lightbulb.readthedocs.io/en/latest/index.html) (very useful place to start)
- [lavaplayer Documentation](https://lavaplayer.readthedocs.io/en/latest/)
- [XJ9 Bot](https://github.com/kamfretoz/XJ9) (inspiration for `error_handler.py` and a few others)
- [kangakari Bot](https://github.com/IkBenOlie5/Kangakari) (inspiration for a few parts)
- [hikari support server](https://discord.gg/Jx4cNGG) (really chill)
