# import speech_recognition as sr

# r = sr.Recognizer()

# with sr.Microphone() as source:
#     print("Speak now:")
#     audio = r.listen(source)

# try:
#     # print("You said: " + r.recognize_google(audio))
#     print(r.recognize_google(audio))


# except sr.UnknownValueError:
#     print("Could not understand audio")
# except sr.RequestError as e:
#     print("Could not request results; {0}".format(e))


import speech_recognition as sr

# initialize recognizer class (for recognizing the speech)
r = sr.Recognizer()

# Reading Microphone as source
# listening the speech and store in audio_text variable
with sr.Microphone() as source:
    print("Talk")
    audio_text = r.listen(source)
    print("Time over, thanks")

# recoginize_() method will throw a request error if the API is unreachable, hence using exception handling
try:
    # using google speech recognition
    print("Text: "+r.recognize_google(audio_text))
except:
    pass