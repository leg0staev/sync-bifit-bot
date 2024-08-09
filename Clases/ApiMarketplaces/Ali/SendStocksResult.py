class SendStocksResult:
    def __init__(self, ok: bool, task_id: str, errors: list[str], external_id: str) -> None:
        self.ok = ok
        self.task_id = task_id
        self.errors = errors
        self.external_id = external_id

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def __repr__(self):
        return f"Result(ok={self.ok}, task_id={self.task_id}, errors={self.errors}, external_id={self.external_id})"