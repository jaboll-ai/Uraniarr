
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
  Background polling of finished downloads, moving files into organized folders by `author/series/book` structure. Following ABS schemes by default. Currently no custimization options
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
        container_name: uraniarr
        build: https://github.com/jaboll-ai/Uraniarr.git#main
        image: uraniarr
        ports:
          - "11562:8000"
        environment:
          - CONFIG_DIR=/config
          # Necessary! change to the book vendor named after the greek muse
          - VENDOR=https://www.t****.de 
        # volumes: #make sure the folder exists on host
        #   - <on-host-config>:/config #e.g. /etc/uraniarr
        #   - <on-host-data>:/data #internal must match data_path in your config

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
