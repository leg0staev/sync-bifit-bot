class Tariffication:
    __slots__ = (
        'current_tariff_rate',
        'current_tariff_type',
        'current_tariff_charge',
        'current_tariff_charge_currency_code',
        'next_tariff_rate',
        'next_tariff_type',
        'next_tariff_charge',
        'next_tariff_starts_at',
        'next_tariff_charge_currency_code'
    )

    def __init__(self, data: dict) -> None:
        self.current_tariff_rate = data.get('current_tariff_rate')
        self.current_tariff_type = data.get('current_tariff_type')
        self.current_tariff_charge = data.get('current_tariff_charge')
        self.current_tariff_charge_currency_code = data.get('current_tariff_charge_currency_code')
        self.next_tariff_rate = data.get('next_tariff_rate')
        self.next_tariff_type = data.get('next_tariff_type')
        self.next_tariff_charge = data.get('next_tariff_charge')
        self.next_tariff_starts_at = data.get('next_tariff_starts_at')
        self.next_tariff_charge_currency_code = data.get('next_tariff_charge_currency_code')
