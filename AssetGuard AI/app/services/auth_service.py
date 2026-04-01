from app.extensions import db
from app.models import User
from app.utils.auth import issue_token
from app.utils.errors import ApiError


class AuthService:
    @staticmethod
    def login(*, email: str, password: str) -> dict:
        """
        Validate credentials and issue a signed token.

        Returns is_first_login so the client can redirect to the
        initial password-setup screen when True.
        """
        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            raise ApiError("Invalid email or password", 401, code="invalid_credentials")

        token = issue_token(user=user)
        return {
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role.value,
                "isFirstLogin": user.is_first_login,
            },
        }

    @staticmethod
    def create_user(*, email: str, password: str, role) -> User:
        """
        Create a user (used by seed and admin API).

        New users created by an admin always start with is_first_login=True
        so that they are forced to set a personal password on first login.
        """
        if User.query.filter_by(email=email).first() is not None:
            raise ApiError("Email already exists", 409, code="email_exists")
        user = User(email=email, role=role, is_first_login=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def change_password(*, user_id: int, current_password: str, new_password: str) -> None:
        """
        Verify current_password then replace with new_password.
        Also clears is_first_login regardless of its current value.

        Raises 401 if current_password is wrong.
        Raises 400 if new_password is blank or identical to current_password.
        """
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            raise ApiError("User not found", 404, code="user_not_found")

        if not user.check_password(current_password):
            raise ApiError("Current password is incorrect", 401, code="invalid_credentials")

        if not new_password:
            raise ApiError("newPassword must not be empty", 400, code="validation_error")

        if current_password == new_password:
            raise ApiError("New password must differ from the current password", 400, code="validation_error")

        user.set_password(new_password)
        user.is_first_login = False
        db.session.commit()

    @staticmethod
    def set_initial_password(*, user_id: int, new_password: str) -> None:
        """
        Set a personal password for a first-time login user and clear the flag.

        Does NOT require the old (temporary) password because the caller is
        already authenticated via their Bearer token.
        Raises 400 if the user has already completed first-login setup.
        """
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            raise ApiError("User not found", 404, code="user_not_found")

        if not user.is_first_login:
            raise ApiError(
                "Initial password has already been set. Use /auth/change-password instead.",
                400,
                code="not_first_login",
            )

        if not new_password:
            raise ApiError("newPassword must not be empty", 400, code="validation_error")

        user.set_password(new_password)
        user.is_first_login = False
        db.session.commit()
