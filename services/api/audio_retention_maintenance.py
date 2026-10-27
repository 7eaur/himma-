"""Run the durable P08 private-audio cleanup queue from a maintenance job."""
import json
from v2_audio_retention import run_audio_maintenance

if __name__ == "__main__":
    print(json.dumps(run_audio_maintenance()))
