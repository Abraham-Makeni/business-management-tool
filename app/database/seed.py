from sqlalchemy import select

from app.database.models.business import Business
from app.database.session import SessionLocal


def ensure_default_business() -> Business:
    with SessionLocal() as session:
        existing = session.scalar(select(Business).limit(1))
        if existing:
            return existing

        business = Business(
            business_name="My Business",
            business_type="Retail Shop",
            phone="",
            location="",
        )
        session.add(business)
        session.commit()
        session.refresh(business)
        return business
