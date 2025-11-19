from pydantic import BaseModel

class SeriesAuthor(BaseModel):
    name: str
    entry_id: str

class UnionSeries(BaseModel):
    series_id: str
    series_ids: list[str]

class ManualGUIDDownload(BaseModel):
    book_key: str
    guid: str = None
    name: str
    download: str = None
    i_idx: int

class BookNzb(BaseModel):
  name: str
  guid: str
  size: str | int
  i_idx: int

class ReturnInteractiveSearch(BaseModel):
    query: str
    nzbs: list[BookNzb]