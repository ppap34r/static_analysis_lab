from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

@dataclass
class LineItem:
    sku: str
    category: str
    unit_price: float
    qty: int
    fragile: bool = False

@dataclass
class Invoice:
    invoice_id: str
    customer_id: str
    country: str
    membership: str
    coupon: Optional[str]
    items: List[LineItem]

class InvoiceService:
    def __init__(self) -> None:
        self._coupon_rate: Dict[str, float] = {
            "WELCOME10": 0.10,
            "VIP20": 0.20,
            "STUDENT5": 0.05
        }

    def _validate(self, inv: Invoice) -> List[str]:
        problems: List[str] = []
        if inv is None:
            problems.append("Invoice is missing")
            return problems
        if not inv.invoice_id:
            problems.append("Missing invoice_id")
        if not inv.customer_id:
            problems.append("Missing customer_id")
        if not inv.items:
            problems.append("Invoice must contain items")
        for it in inv.items:
            if not it.sku:
                problems.append("Item sku is missing")
            if it.qty <= 0:
                problems.append(f"Invalid qty for {it.sku}")
            if it.unit_price < 0:
                problems.append(f"Invalid price for {it.sku}")
            if it.category not in ("book", "food", "electronics", "other"):
                problems.append(f"Unknown category for {it.sku}")
        return problems

    def _calculate_shipping(self, subtotal: float, country: str) -> float:
        """Calculate shipping cost based on subtotal and country."""
        if country == "TH":
            return 0 if subtotal >= 500 else 60
        elif country == "JP":
            return 0 if subtotal >= 4000 else 600
        elif country == "US":
            if subtotal < 100:
                return 15
            elif subtotal < 300:
                return 8
            return 0
        else:
            return 0 if subtotal >= 200 else 25

    def _calculate_tax_rate(self, country: str) -> float:
        """Get tax rate based on country."""
        country_tax_rates = {
            "TH": 0.07,
            "JP": 0.10,
            "US": 0.08
        }
        return country_tax_rates.get(country, 0.05)

    def _calculate_discount(self, membership: str, subtotal: float) -> float:
        """Calculate discount based on membership type."""
        if membership == "gold":
            return subtotal * 0.03
        elif membership == "platinum":
            return subtotal * 0.05
        elif subtotal > 3000:
            return 20
        return 0.0

    def _apply_coupon(self, coupon: Optional[str], subtotal: float, discount: float, warnings: List[str]) -> float:
        """Apply coupon discount if valid."""
        if coupon is None or coupon.strip() == "":
            return discount

        code = coupon.strip()
        if code in self._coupon_rate:
            return discount + subtotal * self._coupon_rate[code]
        
        warnings.append("Unknown coupon")
        return discount

    def compute_total(self, inv: Invoice) -> Tuple[float, List[str]]:
        warnings: List[str] = []
        problems = self._validate(inv)
        if problems:
            raise ValueError("; ".join(problems))

        subtotal = 0.0
        fragile_fee = 0.0
        for it in inv.items:
            line = it.unit_price * it.qty
            subtotal += line
            if it.fragile:
                fragile_fee += 5.0 * it.qty

        shipping = self._calculate_shipping(subtotal, inv.country)
        discount = self._calculate_discount(inv.membership, subtotal)
        discount = self._apply_coupon(inv.coupon, subtotal, discount, warnings)

        tax_rate = self._calculate_tax_rate(inv.country)
        tax = (subtotal - discount) * tax_rate

        total = subtotal + shipping + fragile_fee + tax - discount
        total = max(0.0, total)

        if subtotal > 10000 and inv.membership not in ("gold", "platinum"):
            warnings.append("Consider membership upgrade")

        return total, warnings
