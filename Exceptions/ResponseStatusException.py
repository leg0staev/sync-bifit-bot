from Exceptions.ResponseException import ResponseException


class ResponseStatusException(ResponseException):
    def __init__(self, error) -> None:
        self.error = error

    def __str__(self) -> str:
        return f'Ошибка сервера - {self.error}'
