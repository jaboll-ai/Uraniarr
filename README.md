
<p align="center">
  <img src="frontend/public/assets/lesarr.svg" alt="Lesarr Logo" width="200"/>
</p>

> [!WARNING]
> Doesn't work behind a VPN... yet.. maybe soon(tm)

> [!CAUTION]
> This project is really experimental and might not work/break something on your system. There will be dragons!

# Lesarr

Lesarr is a FastAPI-based application for scraping book metadata from ***REMOVED***, managing authors, series, and editions in a SQLite database via SQLModel, and integrating NZB downloading through SABnzbd. It follows a clean architecture, separating routers, services, and models for maintainability and testability.

## Features

- **Web Scraping**  
  Fetch book editions, author information, and search results using BeautifulSoup and cloudscraper yourself. Because german metadata for books sucks.
- **RESTful API**  
  Routes organized into `tapi`, `mapi`, `api`, and `nzbapi` for scraping, middleware imports, database access, and NZB handling.
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
   docker build . -t lesarr
   ```
3. **(Optional) Docker Compose**  
   Uncomment and adjust volume mounts as needed in `docker-compose.yml`:
   ```yaml
   version: '3.8'
   services:
     lesarr:
       image: lesarr
       ports:
         - "8000:8000"
       # Configure mounts for persistent data:
       # volumes:
       #   - <on_host_config>:/config
       #   - <on_host_data>:/data
   ```
4. **Run the application**  
   - With Docker:  
     ```bash
     docker run -p 8000:8000 \
       -v <on_host_config>:/config \
       -v <on_host_data>:/data \
       lesarr
     ```
   - Or locally:  
     ```bash
     pip install -r requirements.txt
     python entry.py
     ```

## Contributing

Contributions are welcome! Please open issues and submit pull requests.

## License

This project is licensed under the MIT License.
