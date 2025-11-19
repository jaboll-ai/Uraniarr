
<p align="center">
  <img src="frontend/public/assets/uraniarr.svg" alt="Uraniarr Logo" width="200"/>
</p>

> [!WARNING]
> Doesn't work behind a VPN... yet.. maybe soon(tm). The scraping sometimes, repeatedly fails... just try again until it works.

> [!CAUTION]
> This project is really experimental and might not work/break something on your system. There will be dragons!

# Uraniarr

[Uraniarr](https://de.wikipedia.org/wiki/Urania) is an ebook and audiobook collection manager that aims to provide functionality to grab, sort and reorder books and audiobooks in one instance. In an effort to decentralize the metadata, because past projects have proofen this to be the most challenging task, the metadata is scraped/fetched from Vendors, with an attempt to sanitize and clean the data as much as automatically possible before using it.

## Overview
<img width="49%" alt="light-and-dark" src="https://github.com/user-attachments/assets/5472fd32-d5ae-486c-a5d1-0fb581656b7b" />
<img width="49%" alt="light-and-dark-author" src="https://github.com/user-attachments/assets/7ab33591-9ffd-4bea-ac29-2509f133d1cc" />


## Features

- **Downloading**
  Uraniarr currently supports SABnzbd as a downloader.
- **File Management**
  Background polling of finished downloads, moving files into organized folders by `author/series/book` structure. Following ABS schemes by default. For customization see the [Templating Guide](https://github.com/jaboll-ai/Uraniarr/wiki#templating-guide) in the wiki.
- **TODO**
  1. RSS Feed automation
  2. Scan for existing files and sort them into DB
  3. Refining of visuals

## Getting Started
1. **Docker Compose**
   Uncomment and adjust volume mounts as needed in `docker-compose.yml`:
  ```yaml
  services:
    uraniarr:
      image: ghcr.io/jaboll-ai/uraniarr:latest #:development
      container_name: uraniarr
      ports:
        - "11562:8000"
      environment:
        - TZ=Europe/Berlin
        - PUID=1000
        - PGID=1000
        # Necessary! change to the book vendor named after the greek muse
        - VENDOR=https://www.t****.de
        - CONFIG_DIR=/config
        - ACCESS_LOG=false # default: false (Log every API hit in backend)
        - LOG_LEVEL=INFO # default: INFO ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE']
        - ALLOWED_URLS=* # default: * (Should be set if exposed to internet)
        # - ALLOWED_METHODS=* # DEVELOPMENT ONLY
        # - ALLOWED_HEADERS=* # DEVELOPMENT ONLY
      # volumes: #make sure the folder exists on host
      #   - <on-host-config>:/config #e.g. /etc/uraniarr
      #   - <on-host-data>:<internal-data-path> #e.g. /data
      #   - <on-host-libary>:<internal-lib-path> #e.g. /library (if libary is on the same disk as <internal-data-path> this is not needed)
      #
      # ╭────────────────────────────────────────────────────────────────────────────────────────╮
      # │   The <internal-data-path> should match the path of your downloaders mount path        │
      # │ this means if sab reports the download to be in /data but on your host this is mounted │
      # │     at /volume1/sink/downloads then you should mount either the entire /volume1        │
      # │                 (useful when library is on the same disk)                              │
      # │          or mount the exact path like '/volume1/sink/downloads:/data'                  │
      # │                  !! If this confuses you but you followed the                          │
      # │              https://trash-guides.info/File-and-Folder-Structure/                      │
      # │                             it should just work with '/data'!!                         │
      # ╰────────────────────────────────────────────────────────────────────────────────────────╯
```
**ALTERNATIVE: Run the application bare-bones (please don't)**

1. **Build the frontend assets**

   ```bash
     cd frontend && npm install && npm run build && cd ..
   ```
 2. **Start**
    ```bash
    pip install -r requirements.txt
    python entry.py
    ```

## Contributing
1. Create your `venv` and install the `requirements.txt`
2. Run `VENDOR=https://www.t****.de uvicorn backend.main:app --reload`
3. Make a file `frontend/.env.devolopment` with `VITE_API_BASE=http://localhost:<uvicorn-port>`
4. Run Vue with `cd fronted && npm run dev --host`

## License
This project is licensed under the **Mozilla Public License 2.0 (MPL-2.0)**.
