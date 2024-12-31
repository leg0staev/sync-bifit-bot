class FirstMileType:
    __slots__ = ('dropoff_point_id',
                 'dropoff_timeslot_id',
                 'first_mile_is_changing',
                 'first_mile_type')

    def __init__(self, data) -> None:
        self.dropoff_point_id = data.get('dropoff_point_id')
        self.dropoff_timeslot_id = data.get('dropoff_timeslot_id')
        self.first_mile_is_changing = data.get('first_mile_is_changing')
        self.first_mile_type = data.get('first_mile_type')
