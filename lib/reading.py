class Reading:
    def __init__(self, value, unit, description):
        self.value = value
        self.unit = unit
        self.description = description

    def __str__(self):
        return f"{self.value} {self.unit} - {self.description}"