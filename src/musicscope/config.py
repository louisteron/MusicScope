from dataclasses import dataclass
@dataclass(slots=True)
class Config:
    app_name:str='MusicScope'
    version:str='0.1.0'
