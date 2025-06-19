import requests
from phonemizer import phonemize
from phonemizer.separator import Separator
import pyphen
# import pronouncing
from arpa2ipa import arpa_to_ipa
from syllabify import syllabify, pprint
from g2p_en import G2p
import nltk
# nltk.download('averaged_perceptron_tagger_eng')
# nltk.download('cmudict')
from nltk.corpus import cmudict

dic = pyphen.Pyphen(lang="en_US")  # 拼写拆分器

text = [
    # "syllable",
    "syllabify",
]

# cmu = cmudict.dict()
# print('cmu:', cmu[text[0].lower()])

# phn is a list of 190 phonemized sentences
# phn = phonemize(
#     text,
#     language='en-us',
#     backend='festival',
#     separator=Separator(phone=None, word=' ', syllable='|'),
#     strip=True,
#     preserve_punctuation=True,
#     njobs=4)

phn = phonemize(
    text,
    language='en-us',
    backend='espeak',
    # separator=Separator(phone=' ', word=' ')
    )

# phn = phonemize(
#     text,
#     language='en-us',
#     backend='espeak',
#     separator=Separator(phone='|')
# )

print('text:', text)
print('spell:', dic.inserted(text[0]))
# phones = pronouncing.phones_for_word(text[0])
g2p = G2p()
phones = g2p(text[0])
print('phn:', phn)
print('phones:', phones)

example_pron = phones
syllab = syllabify(example_pron)
print('example_pron:', example_pron)
syllabifyd = pprint(syllab)
# 如果第一个字符为-就去掉
if syllabifyd.startswith('-'):
    syllabifyd = syllabifyd[1:]
print('syllabify:', syllabifyd)


# 将arpabet音素转换为IPA: AE1-K.T-IH0-V
# phonesRes1 = arpa_to_ipa('IH0 G')  
# phonesRes2 = arpa_to_ipa('Z AE1 M')  
# phonesRes3 = arpa_to_ipa('P AH0 L')  
# phonesRes1 = arpa_to_ipa('AE1 K')  
# phonesRes2 = arpa_to_ipa('T IH0 V')  

# 音节数组
phonesJoin = syllabifyd.split('.')
# 将phonesJoin数组里的-改为空格
phonesJoin = [phone.replace('-', ' ') for phone in phonesJoin]
phonesRes = []
for phone in phonesJoin:
    phonesRes.append(arpa_to_ipa(phone.strip()))

print("arpa_to_ipa_all:", phonesRes)
