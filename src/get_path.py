from pathlib import Path

def getPath(basename):
    return str((Path(__file__).parent / Path('../models/' + basename)).resolve().absolute())
