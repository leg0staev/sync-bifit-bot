class ItemRating:
    def __init__(self, data) -> None:
        self.rating = data['rating']
        self.reviews_count = data['reviews_count']
        self.reviews_count_text = data['reviews_count_text']
