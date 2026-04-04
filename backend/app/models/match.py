from pydantic import BaseModel

class Match(BaseModel):
    thuisteam: str
    uitteam: str
    aanvangstijd: str | None = None
    wedstrijddatum: str | None = None
    wedstrijdcode: str | None = None
    duration: int | None = None
    field_size: float | None = None
