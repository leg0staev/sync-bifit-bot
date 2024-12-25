class Cancellation:

    __slots__ = ('cancel_reason_id',
                 'cancel_reason',
                 'cancellation_type',
                 'cancelled_after_ship',
                 'affect_cancellation_rating',
                 'cancellation_initiator')

    def __init__(self, data: dict) -> None:
        self.cancel_reason_id = data.get('cancel_reason_id')
        self.cancel_reason = data.get('cancel_reason')
        self.cancellation_type = data.get('cancellation_type')
        self.cancelled_after_ship = data.get('cancelled_after_ship')
        self.affect_cancellation_rating = data.get('affect_cancellation_rating')
        self.cancellation_initiator = data.get('cancellation_initiator')
