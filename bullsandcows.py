import random, string

class BullsAndCows():
    def __init__(self):
        self.__secret = ''.join(random.choice(string.digits) for _ in range(4))

    def guess(self):
        return 0