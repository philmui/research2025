from dataclasses import dataclass

@dataclass
class Citation:
    url: str
    title: str
    snippet: str
    source: str
    