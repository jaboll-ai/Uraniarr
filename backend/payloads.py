from pydantic import BaseModel

class SeriesAuthor(BaseModel):
    name: str
    entry_id: str

class UnionSeries(BaseModel):
    series_id: str
    series_ids: list[str]