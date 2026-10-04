from dataclasses import dataclass


@dataclass
class ResourceEvent:
    resource_id: int
    date: str
    description: str


@dataclass
class Resource:
    events: list[ResourceEvent]
