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

    if config is None:
        config = {}

    # Extract mode and strategy preset from config
    mode = config.pop("_mode", "standard")
    strategy_preset = config.pop("_strategy_preset", None)

    if mode == "blur_center":
        from src.mode_blur_center import process
        success = process(input_path, output_path, video_index,
                          config=config, strategy=strategy_preset)
    elif mode == "fake_player":
        from src.mode_fake_player import process
        success = process(input_path, output_path, video_index,
                          config=config, strategy=strategy_preset)
    elif mode == "sandwich":
        from src.mode_sandwich import process
        success = process(input_path, output_path, video_index,
                          config=config, strategy=strategy_preset)
    elif mode == "concat":
        from src.mode_concat import process
        # concat needs a list of inputs; for single-file tasks, repeat to fill duration
        input_list = config.pop("_input_paths", [input_path])
        success = process(input_list, output_path, video_index,
                          config=config, strategy=strategy_preset)
    else:
        # Standard mode - use category-based strategy (none defaults to handwriting)
        if strategy in ("handwriting", "none"):
            from src.enhanced_handwriting import process
        elif strategy == "emotional":
            from src.enhanced_emotional import process
        elif strategy == "health":
            from src.enhanced_health import process
        else:
            print(f"Unknown strategy: {strategy}", flush=True)
            sys.exit(2)

        success = process(input_path, output_path, video_index,
                          config=config, strategy=strategy_preset)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
