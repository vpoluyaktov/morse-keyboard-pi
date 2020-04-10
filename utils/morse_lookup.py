#!/usr/bin/python3

class MorseLookup:
    morse_code_table = {
        " ":    "/",
        "A":    "·−",
        "B":    "−···",
        "C":    "−·−·",
        "D":    "−··",
        "E":    "·",
        "F":    "··−·",
        "G":    "−−·",
        "H":    "····",
        "I":    "··",
        "J":    "·−−−",
        "K":    "−·−",
        "L":    "·−··",
        "M":    "−−",
        "N":    "−·",
        "O":    "−−−",
        "P":    "·−−·",
        "Q":    "−−·−",
        "R":    "·−·",
        "S":    "···",
        "T":    "−",
        "U":    "··−",
        "V":    "···−",
        "W":    "·−−",
        "X":    "−··−",
        "Y":    "−·−−",
        "Z":    "−−··",
        "1":    "·−−−−",
        "2":    "··−−−",
        "3":    "···−−",
        "4":    "····−",
        "5":    "·····",
        "6":    "−····",
        "7":    "−−···",
        "8":    "−−−··",
        "9":    "−−−−·",
        "0":    "−−−−−",
        "?":    "··−−··",
        ".":    "·−·−·−",
        ",":    "−−··−−",
        "!":    "−·−·−−",
        "'":    "·−−−−·",
        "/":    "−··−·",
        "&":    "·−···",
        ":":    "−−−···",
        ";":    "−·−·−·",
        "+":    "·−·−·",
        "-":    "−····−",
        "\"":   "·−··−·",
        "$":    "···−··−",
        "@":    "·−−·−·",
        "<AA>": "·−·−",
        "<BT>": "−···−"
    }

    def get_code_by_char(self, char):
        if char in self.morse_code_table.keys():
            return self.morse_code_table[char]
        else:
            return ""


    def get_char_by_code(self, morse_string):
        result = "_"
        for char in self.morse_code_table.keys():
            if self.morse_code_table[char] == morse_string:
                result = char
                break
        return result    


if __name__ == "__main__":    
    morse_lookup = MorseLookup()
    print(morse_lookup.get_code_by_char("A"))
    print(morse_lookup.get_char_by_code("−−··"))