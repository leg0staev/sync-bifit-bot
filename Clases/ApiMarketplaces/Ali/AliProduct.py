from Clases.ApiMarketplaces.Ali.AliSku import AliSku


class AliProduct:
    def __init__(self, data):
        self.id = data['id']
        self.ali_created_at = data['ali_created_at']
        self.ali_updated_at = data['ali_updated_at']
        self.category_id = data['category_id']
        self.currency_code = data['currency_code']
        self.delivery_time = data['delivery_time']
        self.owner_member_id = data['owner_member_id']
        self.owner_member_seq = data['owner_member_seq']
        self.freight_template_id = data['freight_template_id']
        self.group_ids = data['group_ids']
        self.main_image_url = data['main_image_url']
        self.main_image_urls = data['main_image_urls']
        self.skus = [AliSku(s) for s in data['sku']]
        self.subject = data['Subject']
