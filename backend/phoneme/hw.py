"""Synthesizes speech from the input string of text or ssml.
Make sure to be working in a virtual environment.

Note: ssml must be well-formed according to:
    https://www.w3.org/TR/speech-synthesis/
"""

from google.cloud import texttospeech

import os

print("HTTPS_PROXY =", os.environ.get("HTTPS_PROXY"))
print("HTTP_PROXY =", os.environ.get("HTTP_PROXY"))

os.environ["HTTP_PROXY"] = "http://192.168.31.20:1080"
os.environ["HTTPS_PROXY"] = "http://192.168.31.20:1080"

# Instantiates a client
client = texttospeech.TextToSpeechClient()

# Set the text input to be synthesized

# ssml_text = """
# <speak>
#   <phoneme alphabet="ipa" ph="pen">pen</phoneme>
# </speak>
# """
# ssml_text = """
# <speak>
#   <phoneme alphabet="ipa" ph="səl">cil</phoneme>
# </speak>
# """
ssml_text = """
<speak>
  <phoneme alphabet="ipa" ph="pɛnsəl">pencil</phoneme>
</speak>
"""

# ssml_text = """
# <speak>
#   <phoneme alphabet="ipa" ph="loʊ">lo</phoneme>
# </speak>
# """

# ssml_text = """
# <speak>
#   <phoneme alphabet="ipa" ph="həloʊ">hello</phoneme>
# </speak>
# """

#   <break time="500ms"/>
#   <phoneme alphabet="ipa" ph="loʊ">lo</phoneme>

# 传入文本 text="Hello, World!"
# 传入ipa ssml=ssml_text
synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)

# Build the voice request, select the language code ("en-US") and the ssml
# voice gender ("neutral")
voice = texttospeech.VoiceSelectionParams(
    language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
)

# Select the type of audio file you want returned
audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

# Perform the text-to-speech request on the text input with the selected
# voice parameters and audio file type
response = client.synthesize_speech(
    input=synthesis_input, voice=voice, audio_config=audio_config
)

# The response's audio_content is binary.
output_name = "output.mp3"
with open(output_name, "wb") as out:
    # Write the response to the output file.
    out.write(response.audio_content)
    print(f'Audio content written to file "{output_name}"')
