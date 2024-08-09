class Category:
    def __init__(self, data: dict[str:str]) -> None:
        self.id = data['id']
        self.name = data['name']
        self.is_v2 = data['is_v2']
        self.parent = data.get('parent')
