from pydantic import BaseModel

class ClubInfo(BaseModel):
    clubnaam: str
    clubcode: str
