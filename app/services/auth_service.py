import hashlib
from datetime import datetime

from sqlalchemy import func, select

from app.database.models.user import User
from app.database.session import SessionLocal


class AuthenticationService:
    """Service for user authentication and password management."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256 with salt."""
        salt = "business_tool_salt_2026"  # In production, use a proper salt per user
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

    @staticmethod
    def hash_pin(pin: str) -> str:
        """Hash a PIN using SHA-256."""
        return hashlib.sha256(pin.encode()).hexdigest()

    def authenticate_user(self, username: str, password_or_pin: str) -> User | None:
        """
        Authenticate a user with username and password/PIN.
        Returns the user if authentication succeeds, None otherwise.
        """
        with SessionLocal() as session:
            user = session.scalar(
                select(User).where(User.username == username, User.status == True)
            )
            if not user:
                return None

            # Check password first
            if user.password_hash == self.hash_password(password_or_pin):
                user.last_login_at = datetime.utcnow()
                session.commit()
                _ = user.role, user.must_change_password, user.username
                session.expunge(user)
                return user

            # Check PIN if password didn't match
            if user.pin_hash and user.pin_hash == self.hash_pin(password_or_pin):
                user.last_login_at = datetime.utcnow()
                session.commit()
                _ = user.role, user.must_change_password, user.username
                session.expunge(user)
                return user

            return None

    def owner_exists(self) -> bool:
        """Check whether an owner account already exists."""
        with SessionLocal() as session:
            return session.scalar(
                select(User).where(User.role == "owner", User.status == True).limit(1)
            ) is not None

    def get_active_owner_count(self) -> int:
        """Return the number of active owner accounts."""
        with SessionLocal() as session:
            return session.scalar(
                select(func.count()).select_from(User).where(User.role == "owner", User.status == True)
            ) or 0

    def get_users_for_business(self, business_id: int) -> list[User]:
        """Return all users for a given business."""
        with SessionLocal() as session:
            users = session.scalars(
                select(User).where(User.business_id == business_id).order_by(User.role, User.name)
            ).all()
            for user in users:
                session.expunge(user)
            return users

    def create_user(
        self,
        business_id: int,
        name: str,
        username: str,
        password: str | None = None,
        pin: str | None = None,
        role: str = "cashier",
        must_change_password: bool = False,
        email: str | None = None,
        phone: str | None = None,
    ) -> User:
        """Create a new user account."""
        if not password and not pin:
            raise ValueError("Either password or PIN must be provided.")

        password_hash = self.hash_password(password) if password else None
        pin_hash = self.hash_pin(pin) if pin else None

        with SessionLocal() as session:
            user = User(
                business_id=business_id,
                name=name,
                username=username,
                password_hash=password_hash,
                pin_hash=pin_hash,
                role=role,
                status=True,
                must_change_password=must_change_password,
                email=email,
                phone=phone,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            session.expunge(user)
            return user

    def update_user_password(self, user_id: int, new_password: str) -> bool:
        """Update a user's password."""
        with SessionLocal() as session:
            user = session.scalar(select(User).where(User.id == user_id))
            if not user:
                return False

            user.password_hash = self.hash_password(new_password)
            user.must_change_password = False
            session.commit()
            return True

    def reset_user_password(self, user_id: int, new_password: str) -> bool:
        """Reset a user's password and require a password change if needed."""
        with SessionLocal() as session:
            user = session.scalar(select(User).where(User.id == user_id))
            if not user:
                return False

            user.password_hash = self.hash_password(new_password)
            user.must_change_password = True
            session.commit()
            return True

    def update_user_pin(self, user_id: int, new_pin: str) -> bool:
        """Update a user's PIN."""
        with SessionLocal() as session:
            user = session.scalar(select(User).where(User.id == user_id))
            if not user:
                return False

            user.pin_hash = self.hash_pin(new_pin)
            session.commit()
            return True

    def disable_user(self, user_id: int) -> bool:
        """Disable a user account."""
        with SessionLocal() as session:
            user = session.scalar(select(User).where(User.id == user_id))
            if not user:
                return False

            if user.role == "owner" and user.status:
                owner_count = session.scalar(
                    select(func.count()).select_from(User).where(User.role == "owner", User.status == True)
                ) or 0
                if owner_count <= 1:
                    return False

            user.status = False
            session.commit()
            return True

    def enable_user(self, user_id: int) -> bool:
        """Enable a user account."""
        with SessionLocal() as session:
            user = session.scalar(select(User).where(User.id == user_id))
            if not user:
                return False

            user.status = True
            session.commit()
            return True
