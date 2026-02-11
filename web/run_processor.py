"""Thin wrapper to run a processor as a subprocess with real-time stdout."""
import json
import sys
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main():
    if len(sys.argv) < 5:
        print("Usage: run_processor.py <strategy> <input> <output> <index> [config_json]", flush=True)
        sys.exit(2)

    strategy = sys.argv[1]
    input_path = sys.argv[2]
    output_path = sys.argv[3]
    video_index = int(sys.argv[4])
    config = json.loads(sys.argv[5]) if len(sys.argv) > 5 else None

    if strategy == "handwriting":
        from src.enhanced_handwriting import process
    elif strategy == "emotional":
        from src.enhanced_emotional import process
    elif strategy == "health":
        from src.enhanced_health import process
    else:
        print(f"Unknown strategy: {strategy}", flush=True)
        sys.exit(2)

    success = process(input_path, output_path, video_index, config=config)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
