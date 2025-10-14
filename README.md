
<p align="center">
  <img src="frontend/public/assets/uraniarr.svg" alt="Uraniarr Logo" width="200"/>
</p>

> [!WARNING]
> Doesn't work behind a VPN... yet.. maybe soon(tm). The scraping sometimes, repeatedly fails... just try again until it works. 

> [!CAUTION]
> This project is really experimental and might not work/break something on your system. There will be dragons!

# Uraniarr

[Uraniarr](https://de.wikipedia.org/wiki/Urania) is a FastAPI-based application for scraping book metadata from a german vendor, managing authors, series, and editions in a SQLite database via SQLModel, and integrating NZB downloading through SABnzbd. It follows a somewhat clean architecture, so if you are interested in contributing, please do so! 

## Features

- **Web Scraping**  
  Fetch book editions, author information, and search results using BeautifulSoup and playwright yourself. Because german metadata for books sucks.
- **RESTful API**  
  Routes organized into `tapi`, `api`, and `nzbapi` for scraping, middleware imports, database access, and NZB handling.
- **Database Integration**  
  SQLite database powered by SQLModel, with automatic table creation and session management.
- **NZB Downloading**  
  Indexer and downloader services integrated with SABnzbd's API to search and queue downloads. If you want other downloaders, write the bridge yourself :)
- **File Management**  
  Background polling of finished downloads, moving files into organized folders by `author/series/book` structure. Following ABS schemes by default. Currently no custimization options

## Getting Started

1. **Build the frontend assets**  
   ```bash
   cd frontend && npm install && npm run build && cd ..
   ```
2. **Build the Docker image**  
   ```bash
   docker build . -t uraniarr
   ```
3. **Docker Compose**  
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
  ```
**ALTERNATIVE: Run the application locally (please don't)** 
1. **Build the frontend assets**  
   ```bash
   cd frontend && npm install && npm run build && cd ..
   ```
   **Optional: Build the Docker image**  
   ```bash
   docker build . -t lesarr
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
This project is licensed under the MIT License.
