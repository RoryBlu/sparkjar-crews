from dataclasses import dataclass
from datetime import datetime


@dataclass
class CrewJobEvent:
    job_id: str
    event_type: str
    event_data: dict
    event_time: datetime


# Additional placeholder models for other imports
@dataclass
class ObjectSchema:
    name: str
    schema: dict


@dataclass
class ClientUsers:
    id: str
    clients_id: str


@dataclass
class ClientSecrets:
    client_id: str
    secret_key: str
    secret_value: str


@dataclass
class BookIngestions:
    id: str
    content: str
