import pyttsx3
import logging
import threading

class TTSEngine:
    def __init__(self):
        self.lock = threading.Lock()

    def speak(self, text):
        if not text:
            return
            
        # Run in a separate thread so we don't block the UI
        # pyttsx3 relies on Windows COM, which is highly thread-sensitive.
        # Initializing the engine inside the thread ensures it works properly.
        def _speak():
            with self.lock:
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                    
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 150)
                    engine.say(text)
                    engine.runAndWait()
                    
                    pythoncom.CoUninitialize()
                except Exception as e:
                    logging.error(f"TTS loop error: {e}")
                    
        threading.Thread(target=_speak, daemon=True).start()
