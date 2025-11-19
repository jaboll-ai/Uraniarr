from backend.dependencies import get_logger
from backend.services.downloader.sab_service import SABDownloader

def downloader_factory(cfg):
    r = {
        False: [],
        True:[]
    }
    for downloader in cfg.downloaders:
        if downloader["type"] == "sab":
            if downloader.get("book"): r[False].append(SABDownloader(downloader, len(r[False])))
            if downloader.get("audio"): r[True].append(SABDownloader(downloader, len(r[True])))
        else:
            get_logger().error(f"Unknown indexer type: {downloader['type']}")
            return
    return r