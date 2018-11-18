#!/usr/bin/env python

import random, string

class BullsAndCows():
    def __init__(self, size):
        digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        self.__secret = ''
        for _ in range(size):
            rnd = random.choice(digits)
            self.__secret += rnd
            digits.remove(rnd)
        print(self.__secret)

    def compare(self, guess):
        bullscows = [0, 0]
        for i in range(len(self.__secret)):
            if guess[i] == self.__secret[i]:
                bullscows[0]+=1;
            elif guess[i] in self.__secret:
                bullscows[1]+=1;
        return bullscows