from app.database.models.user import User


class SessionManager:
    """Manages the current user session."""

    _current_user: User | None = None

    @classmethod
    def login_user(cls, user: User) -> None:
        """Set the current logged-in user."""
        cls._current_user = user

    @classmethod
    def logout_user(cls) -> None:
        """Clear the current user session."""
        cls._current_user = None

    @classmethod
    def get_current_user(cls) -> User | None:
        """Get the current logged-in user."""
        return cls._current_user

    @classmethod
    def is_logged_in(cls) -> bool:
        """Check if a user is currently logged in."""
        return cls._current_user is not None

    @classmethod
    def has_permission(cls, permission: str) -> bool:
        """Check if the current user has a specific permission."""
        if not cls._current_user:
            return False

        from app.services.permissions import ROLE_PERMISSIONS
        user_permissions = ROLE_PERMISSIONS.get(cls._current_user.role, set())
        return permission in user_permissions

    @classmethod
    def get_user_role(cls) -> str | None:
        """Get the role of the current user."""
        return cls._current_user.role if cls._current_user else None
