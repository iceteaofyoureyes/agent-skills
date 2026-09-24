from dataclasses import dataclass


@dataclass
class Visit:
    pet_id: int
    date: str
    description: str


@dataclass
class Pet:
    visits: list[Visit]
