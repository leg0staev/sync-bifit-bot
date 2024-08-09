from Clases.ApiMarketplaces.Vk.Category import Category
from Clases.ApiMarketplaces.Vk.Price import Price
from Clases.ApiMarketplaces.Vk.ItemRating import ItemRating


class VkProduct:
    def __init__(self, data) -> None:
        self.availability = data['availability']
        self.category = Category(data['category'])
        self.description = data['description']
        self.id = data['id']
        self.owner_id = data['owner_id']
        self.price = Price(data['price'])
        self.title = data['title']
        self.date = data['date']
        self.is_owner = data['is_owner']
        self.is_adult = data['is_adult']
        self.thumb_photo = data['thumb_photo']
        self.cart_quantity = data['cart_quantity']
        self.sku = data['sku']
        self.item_rating = ItemRating(data['item_rating'])
