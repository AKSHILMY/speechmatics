from speechmatics.models import *
import speechmatics
import time

# Change to your own file
PATH_TO_FILE = "tests/data/client1.wav"
LANGUAGE = "en"

# Generate an API key at https://portal.speechmatics.com/manage-access/
from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=".env")

API_KEY = os.environ['SPEECHMATICS']
# Create a transcription client from config defaults
sm_client = speechmatics.client.WebsocketClient(API_KEY)

# sm_client.add_event_handler(
#     event_name=ServerMessageType.AddPartialTranscript,
#     event_handler=print,
# )
def event_handler_py(event):
    print(event)


sm_client.add_event_handler(
    event_name=ServerMessageType.SpeakersResult,
    event_handler=event_handler_py,
)

conf = TranscriptionConfig(
    language=LANGUAGE, enable_partials=False, max_delay=1, enable_entities=False,
)

print("Starting transcription (type Ctrl-C to stop):")
with open(PATH_TO_FILE, "rb") as fd:
    try:
        s_time = time.time()
        sm_client.run_synchronously(fd, conf)
        print(f"End time : {time.time()-s_time}")
    except KeyboardInterrupt:
        print("\nTranscription stopped.")
