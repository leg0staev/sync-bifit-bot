from Clases.ApiMarketplaces.Ozon.Cancellation import Cancellation
from Clases.ApiMarketplaces.Ozon.PostingProduct import PostingProduct
from Clases.ApiMarketplaces.Ozon.Requirements import Requirements
from Clases.ApiMarketplaces.Ozon.Tariffication import Tariffication


class Posting:
    __slots__ = ('posting_number', 'order_id', 'order_number', 'status', 'delivery_method', 'tracking_number',
                 'tpl_integration_type', 'in_process_at', 'shipment_date', 'delivering_date', 'cancellation',
                 'customer', 'products', 'addressee', 'barcodes', 'analytics_data', 'financial_data', 'is_express',
                 'requirements', 'parent_posting_number', 'available_actions', 'multi_box_qty', 'is_multibox',
                 'substatus', 'prr_option', 'quantum_id', 'tariffication', 'destination_place_id',
                 'destination_place_name', 'is_presortable', 'pickup_code_verified_at')

    def __init__(self, data: dict) -> None:
        self.posting_number = data.get('posting_number')
        self.order_number = data.get('order_number')
        self.status = data.get('status')
        self.delivery_method = data.get('delivery_method')
        self.tracking_number = data.get('tracking_number')
        self.tpl_integration_type = data.get('tpl_integration_type')
        self.in_process_at = data.get('in_process_at')
        self.shipment_date = data.get('shipment_date')
        self.delivering_date = data.get('delivering_date')
        self.cancellation = Cancellation(data.get('cancellation'))
        self.customer = data.get('customer')
        self.products = {PostingProduct(item) for item in data.get('products')}
        self.addressee = data.get('addressee')
        self.barcodes = data.get('barcodes')
        self.analytics_data = data.get('analytics_data')
        self.financial_data = data.get('financial_data')
        self.is_express = data.get('is_express')
        self.requirements = Requirements(data.get('requirements'))
        self.parent_posting_number = data.get('parent_posting_number')
        self.available_actions = data.get('available_actions')
        self.multi_box_qty = data.get('multi_box_qty')
        self.is_multibox = data.get('is_multibox')
        self.substatus = data.get('substatus')
        self.prr_option = data.get('prr_option')
        self.quantum_id = data.get('quantum_id')
        self.tariffication = Tariffication(data.get('tariffication'))
        self.destination_place_id = data.get('destination_place_id')
        self.destination_place_name = data.get('destination_place_name')
        self.is_presortable = data.get('is_presortable')
        self.pickup_code_verified_at = data.get('pickup_code_verified_at')
