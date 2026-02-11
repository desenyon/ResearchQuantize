from dataclasses import dataclass
from typing import Optional


@dataclass
class Author:
    name: str
    affiliation: Optional[str] = None
    email: Optional[str] = None
