class Currency:
    def __init__(self, data) -> None:
        self.id = data['id']
        self.name = data['name']
        self.title = data['title']
        