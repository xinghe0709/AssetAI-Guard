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
