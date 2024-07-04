from dataclasses import dataclass
from enum import Enum

class IdentifierContext(Enum):
    EBOOK = "ebook"
    HARDBACK = "hardback"
    PAPERBACK = "paperback"
    PRINT = "print"
    SOURCE = "source"
    UNKNOWN = "unknown"

class IdentifierType(Enum):
    ISBN = "isbn"
    LCCN = "lccn"
    UNKNOWN = "unknown"

@dataclass(frozen=True)
class Identifier:
    '''Represents a book identifier such as an ISBN'''
    id: str
    type: "IdentifierType"
    context: "IdentifierContext"

    @property
    def id_len(self):
        return len(self.id)
