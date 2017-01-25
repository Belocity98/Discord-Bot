from discord.ext import commands
import discord.utils

import json
import sys, os

def open_json(loadtype : str, file : str):
    app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    try:
        tmp_file = os.path.join(app_path, file)
        with open(tmp_file) as fp:
            if loadtype == "load":
                return json.load(fp)
            if loadtype == "loads":
                return json.loads(fp)
    except:
        pass
