from dataclasses import dataclass, field


@dataclass
class Order:
    id: str
    title: str
    description: str
    url: str
    source: str
    price: str = ""
