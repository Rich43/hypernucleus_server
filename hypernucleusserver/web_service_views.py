from cornice.service import Service
from hypernucleusserver.lib.gamedeplib import GameDepLib

auth = Service(name='gamedep', path='/api/gamedep/{type}/item/{page_id}',
               description="User login and list")

@auth.get()
def api_gamedep(request):
    """Gets all data from the gamedep's page."""
    gamedeptype = request.matchdict.get('type')
    page_id = request.matchdict.get('page_id')
    g = GameDepLib(gamedeptype)
    dbpage, dbrevision = g.show(page_id, None, False)
    result = dbpage.to_dict()
    result["versions"] = {}
    for rev in dbpage.revisions:
        result["versions"][rev.version] = rev.to_dict()
    return result