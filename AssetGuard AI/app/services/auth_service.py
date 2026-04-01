from app.extensions import db
from app.models import User
from app.utils.auth import issue_token
from app.utils.errors import ApiError


class AuthService:
    @staticmethod
    def login(*, email: str, password: str) -> dict:
        """
        Validate credentials and issue a signed token.

        The controller handles HTTP parsing; this layer loads the user,
        checks the password, and builds the token + minimal user payload.
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
            },
        }

    @staticmethod
    def create_user(*, email: str, password: str, role) -> User:
        """
        Create a user (used by seed and admin API).

        Email uniqueness is enforced in the DB; this check returns a clearer API error.
        """
        if User.query.filter_by(email=email).first() is not None:
            raise ApiError("Email already exists", 409, code="email_exists")
        user = User(email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def change_password(*, user_id: int, current_password: str, new_password: str) -> None:
        """
        Verify current_password then replace with new_password.

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
        db.session.commit()
