from Clases.ApiMarketplaces.Ozon.FirstMileType import FirstMileType


class Warehouse:
    def __init__(self, data) -> None:
        self.id = data['warehouse_id']
        self.name = data['name']
        self.is_rfbs = data['is_rfbs']
        self.is_able_to_set_price = data['is_able_to_set_price']
        self.has_entrusted_acceptance = data['has_entrusted_acceptance']
        self.first_mile_type = FirstMileType(data['first_mile_type'])
        self.is_kgt = data['is_kgt']
        self.can_print_act_in_advance = data['can_print_act_in_advance']
        self.min_working_days = data['min_working_days']
        self.is_karantin = data['is_karantin']
        self.has_postings_limit = data['has_postings_limit']
        self.postings_limit = data['postings_limit']
        self.working_days = data['working_days']
        self.min_postings_limit = data['min_postings_limit']
        self.is_timetable_editable = data['is_timetable_editable']
        self.status = data['status']

    # def get_id(self) -> int:
    #     return self.__warehouse_id
    #
    # def get_status(self) -> str:
    #     return self.__status
