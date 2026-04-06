class UserNotFoundError(Exception):
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        super().__init__(f"User id={user_id} not found")


class InvalidCredentialsError(Exception):
    pass


class InvalidTokenError(Exception):
    pass
