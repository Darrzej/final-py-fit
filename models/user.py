# Replace content in models/user.py
class Person:
    def __init__(self, age, height, weight):
        self.age = age
        self.height = height
        self.weight = weight

class User(Person):
    def __init__(self, id, username, age, height, weight, goal, frequency):
        # Using super() for Inheritance
        super().__init__(age, height, weight)
        self.id = id
        self.username = username
        self.goal = goal
        self.frequency = frequency

    @property
    def bmi(self):
        """Calculates BMI as a helper property."""
        return round(self.weight / ((self.height / 100) ** 2), 2)