from pathlib import Path
import shutil

import kagglehub


DATASET = "olistbr/brazilian-ecommerce"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DESTINATION = PROJECT_ROOT / "data" / "raw" / "olist"


def main():
    print("Downloading Olist dataset...")

    dataset_path = Path(
        kagglehub.dataset_download(DATASET)
    )

    DESTINATION.mkdir(parents=True, exist_ok=True)

    csv_files = list(dataset_path.glob("*.csv"))

    for csv_file in csv_files:
        target = DESTINATION / csv_file.name
        shutil.copy2(csv_file, target)
        print(f"Copied: {csv_file.name}")

    print(f"\nFinished: {len(csv_files)} CSV files")
    print(f"Destination: {DESTINATION}")


if __name__ == "__main__":
    main()
