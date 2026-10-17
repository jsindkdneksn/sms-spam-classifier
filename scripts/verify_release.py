import argparse
from pathlib import Path

from app.predictor import Predictor

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, default=Path("models/release"))
    parser.add_argument("--require-release", action="store_true")
    args = parser.parse_args()
    Predictor(
        args.model_dir / "model.joblib",
        args.model_dir / "metadata.json",
        require_release=args.require_release,
    )
    print("Model checksum, prediction contract and provenance checks passed.")
