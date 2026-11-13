from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Product:
    kind: str
    id: int
    name: str
    price: int | None
    original_price: int | None = None
    discount: int = 0
    currency: str = "KRW"
    country: str = "KR"
    collected_at: str = field(default_factory=utcnow)
    scan_id: str = ""
    app_type: str = ""
    app_ids: list[int] = field(default_factory=list)
    contents: list[dict] = field(default_factory=list)
    composition_verified: bool = False
    unconditional: bool = False
    evidence: str = ""
    sale_end: str | None = None

    @property
    def url(self):
        return f"https://store.steampowered.com/{self.kind}/{self.id}/?cc=kr"

    def to_dict(self):
        return {**asdict(self), "url": self.url}
