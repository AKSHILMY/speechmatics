import speechmatics
from httpx import HTTPStatusError
import asyncio
import wave
from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=".env")

API_KEY = os.environ['SPEECHMATICS']
LANGUAGE = "en"
CONNECTION_URL = f"wss://eu2.rt.speechmatics.com/v2/{LANGUAGE}"
CHUNK_SIZE = 1024

class AudioProcessor:
    def __init__(self):
        self.wave_data = bytearray()
        self.read_offset = 0

    async def read(self, chunk_size):
        while self.read_offset + chunk_size > len(self.wave_data):
            await asyncio.sleep(0.001)  # Non-blocking wait for data
        new_offset = self.read_offset + chunk_size
        data = self.wave_data[self.read_offset:new_offset]
        self.read_offset = new_offset
        return data

    def write_audio(self, data):
        self.wave_data.extend(data)

audio_processor = AudioProcessor()

# Stream audio from a file
async def stream_audio_from_file(file_path):
    start = time.process_time()
    with wave.open(file_path, 'rb') as wf:
        chunk = wf.readframes(CHUNK_SIZE)
        while chunk:
            audio_processor.write_audio(chunk)
            chunk = wf.readframes(CHUNK_SIZE)
            await asyncio.sleep(0.01)  # Allow event loop to handle other tasks
    print(time.process_time()-start)
# Define connection parameters
conn = speechmatics.models.ConnectionSettings(
    url=CONNECTION_URL,
    auth_token=API_KEY,
)

# Create a transcription client
ws = speechmatics.client.WebsocketClient(conn)

# Define transcription parameters
conf = speechmatics.models.TranscriptionConfig(
    language=LANGUAGE,
    enable_partials=True,
    max_delay=5,
)

# Define an event handler to print the partial transcript
def print_partial_transcript(msg):
    print(f"[partial] {msg['metadata']['transcript']}")

import time
# Define an event handler to print the full transcript
def print_transcript(msg):
    print(f"[  FINAL: {msg['metadata']['transcript']}")

# Register the event handler for partial transcript
ws.add_event_handler(
    event_name=speechmatics.models.ServerMessageType.AddPartialTranscript,
    event_handler=print_partial_transcript,
)

ws.add_event_handler(
    event_name=speechmatics.models.ServerMessageType.AddTranscript,
    event_handler=print_transcript,
)

settings = speechmatics.models.AudioSettings()
settings.encoding = "pcm_f32le"
settings.sample_rate = 16000
settings.chunk_size = CHUNK_SIZE

async def main():
    # Concurrent tasks: audio streaming + transcription
    audio_task = asyncio.create_task(stream_audio_from_file("/home/akshilmy/coachello/testing/speechamatics/tests/data/coach.wav"))
    try:
        await ws.run(audio_processor, conf, settings)
    finally:
        await audio_task  # Ensure task finishes correctly

# Fix for running inside environments that already have a loop running (like Jupyter)
def run_in_existing_loop(coro):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        return asyncio.create_task(coro)
    else:
        asyncio.run(coro)

if __name__ == "__main__":
    try:
        run_in_existing_loop(main())
    except KeyboardInterrupt:
        print("\nTranscription stopped.")
    except HTTPStatusError as e:
        if e.response.status_code == 401:
            print('Invalid API key - Check your API_KEY at the top of the code!')
        else:
            raise e
