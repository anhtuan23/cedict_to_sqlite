# https://stackoverflow.com/a/21488584
import re

pinyinToneMarks = {
    'a': 'āáǎà', 'e': 'ēéěè', 'i': 'īíǐì',
    'o': 'ōóǒò', 'u': 'ūúǔù', 'ü': 'ǖǘǚǜ',
    'A': 'ĀÁǍÀ', 'E': 'ĒÉĚÈ', 'I': 'ĪÍǏÌ',
    'O': 'ŌÓǑÒ', 'U': 'ŪÚǓÙ', 'Ü': 'ǕǗǙǛ'
}


def convertPinyinCallback(match: Match):
    # group 3 is number tone ([12345])
    tone = int(match.group(3)) % 5
    # group 1 is vowels
    vowels = match.group(1).replace('v', 'ü').replace('V', 'Ü')
    # for multple vowels, use first one if it is a/e/o, otherwise use second one
    pos = 0
    if len(vowels) > 1 and not vowels[0] in 'aeoAEO':
        pos = 1
    if tone != 0:
        vowels = vowels[0:pos] + \
            pinyinToneMarks[vowels[pos]][tone-1] + \
            vowels[pos+1:]
    # group 3 are consonants after the vowels
    return vowels + match.group(2)


def convert_pinyin(string):
    # Convert from number accent to symbol accent
    # Match from vowel to end of word
    return re.sub(r'([aeiouüvÜ]{1,3})(n?g?r?)([012345])', convertPinyinCallback, string, flags=re.IGNORECASE)
