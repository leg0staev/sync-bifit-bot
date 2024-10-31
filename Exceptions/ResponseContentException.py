from Exceptions.ResponseException import ResponseException


class ResponseContentException(ResponseException):
    def __Init__(self, response: str) -> None:
        self.response = response

    def __str__(self) -> str:
        return f'неожиданный ответ сервера: {self.response}'
