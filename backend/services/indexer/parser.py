from backend.dependencies import get_logger
from backend.services.indexer.newznab_service import NewznabService
from backend.services.indexer.prowlarr_service import ProwlarrService


def indexer_factory(cfg):
    r = {
        False: [],
        True:[]
    }
    for indexer in cfg.indexers:
        if indexer["type"] == "newznab":
            if indexer.get("book"): r[False].append(NewznabService(indexer, len(r[False])))
            if indexer.get("audio"): r[True].append(NewznabService(indexer, len(r[True])))
        elif indexer["type"] == "prowlarr":
            if indexer.get("book"): r[False].append(ProwlarrService(indexer, len(r[False])))
            if indexer.get("audio"): r[True].append(ProwlarrService(indexer, len(r[True])))
        else:
            get_logger().error(f"Unknown indexer type: {indexer['type']}")
            return
    return r