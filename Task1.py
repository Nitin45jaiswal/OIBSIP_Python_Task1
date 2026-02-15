import datetime
import webbrowser
import wikipedia
import pyttsx3
import speech_recognition as sr

import sounddevice as sd
import numpy as np
from scipy.signal import resample
import scipy.io.wavfile as wav
import os


class PushToTalkAssistant:
    def __init__(self):
        # TTS (Offline)
        self.engine = pyttsx3.init(driverName="sapi5")
        self.engine.setProperty("rate", 175)
        self.engine.setProperty("volume", 1.0)

        # Speech Recognition
        self.recognizer = sr.Recognizer()

        # Audio settings
        self.device_index = 9   # change to 1 if needed
        self.fs_record = 48000  # laptop mic
        self.fs_google = 16000  # better for recognition

        self.temp_file = "temp.wav"

    def say(self, text):
        print("Assistant:", text)
        self.engine.say(text)
        self.engine.runAndWait()

    def record_audio(self, seconds=4):
        sd.default.device = (self.device_index, None)

        audio = sd.rec(
            int(seconds * self.fs_record),
            samplerate=self.fs_record,
            channels=1,
            dtype=np.int16
        )
        sd.wait()

        return audio.flatten().astype(np.int16)

    def speech_to_text(self, audio_int16):
        # Convert to float for processing
        audio_float = audio_int16.astype(np.float32)

        # Auto gain control
        peak = np.max(np.abs(audio_float)) + 1e-8
        target_peak = 12000.0
        gain = target_peak / peak
        gain = max(0.5, min(gain, 6.0))

        audio_float *= gain
        audio_float = np.clip(audio_float, -32768, 32767)

        # Resample 48k -> 16k for Google SR
        new_len = int(len(audio_float) * self.fs_google / self.fs_record)
        audio_16k = resample(audio_float, new_len).astype(np.int16)

        print("Input level:", int(np.max(np.abs(audio_16k))))

        # Save temp wav
        wav.write(self.temp_file, self.fs_google, audio_16k)

        # Recognize using Google
        try:
            with sr.AudioFile(self.temp_file) as source:
                audio_data = self.recognizer.record(source)

            text = self.recognizer.recognize_google(audio_data, language="en-IN")
            return text.lower().strip()

        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            self.say("Network issue. Please check your internet.")
            return ""
        finally:
            if os.path.exists(self.temp_file):
                os.remove(self.temp_file)

    def current_time(self):
        now = datetime.datetime.now().strftime("%I:%M %p")
        self.say(f"The time is {now}")

    def current_date(self):
        today = datetime.datetime.now().strftime("%d %B %Y")
        self.say(f"Today's date is {today}")

    def wiki_search(self, topic):
        try:
            self.say("Searching Wikipedia.")
            summary = wikipedia.summary(topic, sentences=2)
            self.say(summary)
        except:
            self.say("I could not find a proper result on Wikipedia.")

    def google_search(self, query):
        self.say("Searching on Google.")
        webbrowser.open(f"https://www.google.com/search?q={query}")

    def open_website(self, name):
        sites = {
            "youtube": "https://www.youtube.com",
            "google": "https://www.google.com",
            "gmail": "https://mail.google.com"
        }
        if name in sites:
            self.say(f"Opening {name}")
            webbrowser.open(sites[name])
        else:
            self.say("Website not found.")

    def handle_command(self, command):
        if not command:
            self.say("I could not understand. Please try again.")
            return

        print("You said:", command)

        if "hello" in command or "hi" in command:
            self.say("Hello! How are you?")

        elif "time" in command:
            self.current_time()

        elif "date" in command:
            self.current_date()

        elif "open youtube" in command:
            self.open_website("youtube")

        elif "open google" in command:
            self.open_website("google")

        elif "open gmail" in command:
            self.open_website("gmail")

        elif "wikipedia" in command:
            self.say("Tell me the topic.")
            topic = input("Topic: ").strip()
            if topic:
                self.wiki_search(topic)

        elif "search" in command:
            self.say("What should I search?")
            query = input("Search: ").strip()
            if query:
                self.google_search(query)

        elif "exit" in command or "stop" in command or "quit" in command:
            self.say("Goodbye. Take care.")
            raise SystemExit

        else:
            self.say("I am not trained for that command yet.")

    def start(self):
        self.say("Hello! Push to talk mode is enabled.")
        print("\nPush-To-Talk Assistant Started.")
        print("Press ENTER to speak. Type 'exit' to stop.\n")

        while True:
            user_key = input("Press ENTER to speak (or type exit): ").strip().lower()

            if user_key == "exit":
                self.say("Goodbye. Take care.")
                break

            print("Speak now...")
            audio = self.record_audio(seconds=4)
            command = self.speech_to_text(audio)

            self.handle_command(command)


if __name__ == "__main__":
    bot = PushToTalkAssistant()
    bot.start()
