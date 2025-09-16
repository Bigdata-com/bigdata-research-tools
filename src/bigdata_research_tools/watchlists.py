from collections import namedtuple

from bigdata_client.models.watchlists import Watchlist
from bigdata_client import Bigdata

from bigdata_research_tools.utils.distance import levenshtein_distance

def fuzzy_find_watchlist_by_name(name: str, bigdata: Bigdata, only_private: bool = False, max_distance: int = 2) -> Watchlist | None:
    watchlists = bigdata.watchlists.list(owned=only_private)
    WlScore = namedtuple("WlScore", ["watchlist", "score"])
    scored_list: list[WlScore] = []
    for wl in watchlists:
        wl_scored = WlScore(wl, levenshtein_distance(wl.name.lower(), name.lower()))
        if wl_scored.score <= max_distance:
            scored_list.append(wl_scored)

    if len(scored_list) == 0:
        return None

    # Sort by score
    scored_list.sort(key=lambda x: x.score)
    return scored_list[0].watchlist

def find_watchlist_by_name(name: str, bigdata: Bigdata, only_private: bool = False) -> Watchlist | None:
    watchlists = bigdata.watchlists.list(owned=only_private)
    for wl in watchlists:
        if wl.name.lower() == name.lower():
            return wl
    return None

def create_watchlist(name: str, company_names: list[str], bigdata: Bigdata) -> Watchlist:
    """Create a watchlist with the given name from a list of company names.
    """
    if find_watchlist_by_name(name, bigdata, only_private=True):
        raise ValueError(f"You already have access to a Watchlist with name '{name}'.")
    entity_list = []
    for company_name in company_names:
        bigdata.knowledge_graph.find_companies(company_name, limit=1)
        entity_list.append(bigdata.knowledge_graph.find_companies(company_name, limit=1)[0])
    return bigdata.watchlists.create(name=name, items=[e.id for e in entity_list])
