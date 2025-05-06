from Clases.ApiMarketplaces.Vk.Category import Category
from Clases.ApiMarketplaces.Vk.Price import Price
from Clases.ApiMarketplaces.Vk.ItemRating import ItemRating


class VkProduct:
    def __init__(self, data) -> None:
        self.availability = data.get('availability')
        self.category = Category(data['category'])
        self.description = data.get('description')
        self.id = data.get('id')
        self.owner_id = data.get('owner_id')
        self.price = Price(data.get('price'))
        self.title = data.get('title')
        self.date = data.get('date')
        self.is_owner = data.get('is_owner')
        self.is_adult = data.get('is_adult')
        self.thumb_photo = data.get('thumb_photo')
        self.cart_quantity = data.get('cart_quantity')
        self.sku = data.get('sku')
        self.csrf_hashes = data.get('csrf_hashes')
        self.thumb = data.get('thumb')
        self.has_group_access = data.get('has_group_access')
        self.market_url = data.get('market_url')
        self.item_rating = ItemRating(data.get('item_rating'))

    def __repr__(self):
        return (f'имя ВК товара - {self.title}\n'
                f'штрихкод ВК товара - {self.sku}\n'
                f'ID ВК товара - {self.id}')


    def __eq__(self, other):
        if isinstance(other, VkProduct):
            return self.id == other.id
        return False

    def __hash__(self):
        return hash(self.id)