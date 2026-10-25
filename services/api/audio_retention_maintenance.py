"""Run the durable P08 private-audio cleanup queue from a maintenance job."""
import json
from v2_audio_retention import process_queued_audio_purges

if __name__ == "__main__":
    print(json.dumps(process_queued_audio_purges(limit=100)))
