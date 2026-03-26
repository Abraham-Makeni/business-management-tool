from sqlalchemy import select

from app.database.models.business import Business
from app.database.models.user import User
from app.database.session import SessionLocal
from app.services.auth_service import AuthenticationService


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


def ensure_default_owner() -> User:
    """Ensure a default owner account exists."""
    business = ensure_default_business()

    with SessionLocal() as session:
        existing = session.scalar(select(User).where(User.role == "owner").limit(1))
        if existing:
            return existing

        auth_service = AuthenticationService()
        owner = auth_service.create_user(
            business_id=business.id,
            name="Owner",
            username="owner",
            password="admin123",  # Default password, should be changed
            role="owner",
            must_change_password=True
        )
        return owner
