from dataclasses import dataclass, fields, MISSING


@dataclass(
    order=True,
)
class Address:
    recipient: str
    zip_code: str
    city: str
    street: str
    street_no: str
    country: str

    @classmethod
    def required_fields(cls):
        return [f.name for f in fields(cls) if f.default == MISSING]
