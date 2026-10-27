
from src.database import SessionLocal
from src.models import Offer

db = SessionLocal()

try:
    print("=== OFFERS NOT YET ISSUED ===")

    offers = (
        db.query(Offer)
        .order_by(Offer.offer_id)
        .all()
    )

    for offer in offers:
        status = getattr(offer.status, "value", str(offer.status))
        if status not in ("ISSUED", "ACCEPTED", "REJECTED", "EXPIRED"):
            print(f"Offer ID: {offer.offer_id} | Status: {status}")

    print("\n=== TOTAL OFFERS ===", len(offers))

finally:
    db.close()
