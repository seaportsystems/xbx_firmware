import time

def struct_time_to_iso8601(struct_time):
    year, month, day, hour, minute, second, _, _, _ = struct_time

    # Format to ISO8601 using f-string
    return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}"

class Reading:
    def __init__(self, value, unit, description):
        self.value = value
        self.unit = unit
        self.description = description
        self.datetime = struct_time_to_iso8601(time.localtime())

    def __str__(self):
        return f"{self.value} {self.unit} - {self.description}"