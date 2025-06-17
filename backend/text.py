import requests
from phonemizer import phonemize
from phonemizer.separator import Separator

text = [
    "industry",
]

# phn is a list of 190 phonemized sentences
phn = phonemize(
    text,
    # 英式英语
    language='en-us',  # 'en-us' for American English
    backend='festival',
    separator=Separator(phone=None, word=' ', syllable='|'),
    strip=True,
    preserve_punctuation=True,
    njobs=4)

# phn = phonemize(
#     text,
#     language='en-us',
#     backend='espeak',
#     separator=Separator(phone=None, word=' ', syllable='|'))

# phn = phonemize(
#     text,
#     language='en-us',
#     backend='espeak',
#     separator=Separator(phone='|')
# )

print('text:', text)
print('phn:', phn)

def split_festival_syllable(syl: str, phoneset: set) -> list[str]:
    i = 0
    phonemes = []
    while i < len(syl):
        # 优先匹配2字符音素
        if i + 1 < len(syl) and syl[i:i+2] in phoneset:
            phonemes.append(syl[i:i+2])
            i += 2
        elif syl[i] in phoneset:
            phonemes.append(syl[i])
            i += 1
        else:
            # fallback 保留原字符
            phonemes.append(syl[i])
            i += 1
    return phonemes


import re
from typing import List, Set


class InternationalPhoneticAlphabet:
    us_phone_set_to_ipa = {
        # http://www.festvox.org/bsv/c4711.html
        # https://en.m.wikipedia.org/wiki/ARPABET
        # I think this is wrong. A help from a language specialist is welcome!
        "aa": "ɑ",
        "ae": "æ",
        "ah": "ə",
        "ao": "ɔ",
        "aw": "aʊ",
        "ax": "ə", # active: aek|taxv => æk|təv
        "ay": "aɪ",
        "eh": "ɛ",
        "el": "l̩",
        "em": "m̩",
        "en": "n̩",
        "er": "ər",
        "ey": "eɪ",
        "ih": "ɪ",
        "iy": "i",
        "ow": "oʊ",
        "oy": "ɔɪ",
        "uh": "ʊ",
        "uw": "u",
        "b": "b",
        "ch": "ʧ",
        "d": "d",
        "dh": "ð",
        "f": "f",
        "g": "ɡ",
        "hh": "h",
        "jh": "ʤ",
        "k": "k",
        "l": "l",
        "m": "m",
        "n": "n",
        "ng": "ŋ",
        "p": "p",
        "r": "r", #industry: "ɪnˈdʌstri" => "ɪnˈdʌstɹi"
        "s": "s",
        "sh": "ʃ",
        "t": "t",
        "th": "θ",
        "v": "v",
        "w": "w",
        "y": "j",
        "z": "z",
        "zh": "ʒ",
        "pau": "",
    }

    regex_to_capture_ipa_stress_mark = r"([\ˈ\ˌ])"

    @classmethod
    def ipa_format_from_us_phone_set(cls, phonemes: list[str]) -> list[str]:
        phonemes_as_ipa_symbols = []

        for index, phoneme in enumerate(phonemes):
            matches = list(re.finditer(cls.regex_to_capture_ipa_stress_mark, phoneme))
            if not matches:
                ipa_version = cls.us_phone_set_to_ipa[phoneme]
                phonemes_as_ipa_symbols.append(ipa_version)
            else:
                match = matches[0]
                mark_that_was_matched = match.group()
                phoneme_without_stress = phoneme[match.end() :]
                ipa_version = cls.us_phone_set_to_ipa[phoneme_without_stress]
                final_ipa_version = f"{ipa_version}{mark_that_was_matched}"
                phonemes_as_ipa_symbols.append(final_ipa_version)

        return phonemes_as_ipa_symbols

# 输出
syllables = phn[0].split("|")
phoneset = set(InternationalPhoneticAlphabet.us_phone_set_to_ipa.keys())

ipa_all = []

for syl in syllables:
    phones = split_festival_syllable(syl, phoneset)
    ipa = InternationalPhoneticAlphabet.ipa_format_from_us_phone_set(phones)
    ipa_all.append("".join(ipa))

print("|".join(ipa_all))  # 输出：ɪg|zæm|pəl