class FirstMileType:
    def __init__(self, data) -> None:
        self.dropoff_point_id = data['dropoff_point_id']
        self.dropoff_timeslot_id = data['dropoff_timeslot_id']
        self.first_mile_is_changing = data['first_mile_is_changing']
        self.first_mile_type = data['first_mile_type']
