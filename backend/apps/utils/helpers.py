from dataclasses import dataclass


@dataclass
class Address:
    first_name: str
    last_name: str
    street: str
    street_no: str
    zip_code: str
    city: str
    country: str

    @property
    def recipient(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def as_checkout_shipping(self) -> dict:
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "street": self.street,
            "street_no": self.street_no,
            "zip": self.zip_code,
            "city": self.city,
            "country": self.country,
        }
