#!/usr/bin/env python

import random, string

class BullsAndCows():
    def __init__(self, size):
        self.__secret = ''.join(random.choice(string.digits) for _ in range(size))

    def compare(self, guess):
        if len(guess) != len(self.__secret):
            return 'Error, the guess length has to be ' + len(self.__secret)
        bullscows = [0, 0]
        for i in range(len(self.__secret)):
            if guess[i] == self.__secret[i]:
                bullscows[0]+=1;
            elif guess[i] in self.__secret:
                bullscows[1]+=1;
        return bullscows