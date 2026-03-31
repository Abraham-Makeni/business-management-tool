from datetime import datetime

import bcrypt
from sqlalchemy import func, select

from app.database.models.user import User
from app.database.session import SessionLocal


class AuthenticationService:
    """Service for user authentication and password management."""

    _legacy_salt = "business_tool_salt_2026"

    @staticmethod
    def _looks_like_legacy_sha256_hash(value: str | None) -> bool:
        if not value:
            return False
        if len(value) != 64:
            return False
        try:
            int(value, 16)
        except ValueError:
            return False
        return True

    @staticmethod
    def _legacy_hash_password(password: str) -> str:
        import hashlib

        return hashlib.sha256(f"{AuthenticationService._legacy_salt}{password}".encode()).hexdigest()

    @staticmethod
    def _legacy_hash_pin(pin: str) -> str:
        import hashlib

        return hashlib.sha256(pin.encode()).hexdigest()

    @classmethod
    def hash_password(cls, password: str) -> str:
        """Hash a password using bcrypt."""
        # Truncate password to 72 bytes as required by bcrypt
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    @classmethod
    def hash_pin(cls, pin: str) -> str:
        """Hash a PIN using bcrypt."""
        pin_bytes = pin.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(pin_bytes, salt).decode('utf-8')

    def authenticate_user(self, username: str, password_or_pin: str) -> User | None:
        """
        Authenticate a user with username and password/PIN.
        Returns the user if authentication succeeds, None otherwise.
        """
        if len(password_or_pin) > 256:
            # Prevent pathological input sizes from degrading performance.
            return None

        with SessionLocal() as session:
            user = session.scalar(
                select(User).where(User.username == username, User.status == True)
            )
            if not user:
                return None

            def _finalize_login() -> User:
                user.last_login_at = datetime.utcnow()
                session.commit()
                session.expunge(user)
                return user

            # Check password first (bcrypt or legacy sha256)
            if user.password_hash:
                if self._looks_like_legacy_sha256_hash(user.password_hash):
                    if user.password_hash == self._legacy_hash_password(password_or_pin):
                        # Upgrade legacy hash -> bcrypt
                        user.password_hash = self.hash_password(password_or_pin)
                        return _finalize_login()
                else:
                    # Verify bcrypt password hash
                    try:
                        password_bytes = password_or_pin.encode('utf-8')
                        if len(password_bytes) > 72:
                            password_bytes = password_bytes[:72]
                        if bcrypt.checkpw(password_bytes, user.password_hash.encode('utf-8')):
                            return _finalize_login()
                    except (ValueError, TypeError):
                        pass

            # Check PIN if password didn't match
            if user.pin_hash:
                if self._looks_like_legacy_sha256_hash(user.pin_hash):
                    if user.pin_hash == self._legacy_hash_pin(password_or_pin):
                        user.pin_hash = self.hash_pin(password_or_pin)
                        return _finalize_login()
                else:
                    # Verify bcrypt PIN hash
                    try:
                        pin_bytes = password_or_pin.encode('utf-8')
                        if len(pin_bytes) > 72:
                            pin_bytes = pin_bytes[:72]
                        if bcrypt.checkpw(pin_bytes, user.pin_hash.encode('utf-8')):
                            return _finalize_login()
                    except (ValueError, TypeError):
                        pass

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
