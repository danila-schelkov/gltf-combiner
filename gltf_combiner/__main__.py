import os
from pathlib import Path

from gltf_combiner import build_combined_gltf, collect_files_info
from gltf_combiner.gltf.exceptions import AnimationNotFoundException

TEST_RESOURCES_PATH = Path("../test/resources")


def main() -> None:
    input_directory = TEST_RESOURCES_PATH
    output_directory = Path("../test/combined/")
    os.makedirs(input_directory, exist_ok=True)
    os.makedirs(output_directory, exist_ok=True)

    collected_files = collect_files_info(input_directory)
    for file_info in collected_files:
        if len(file_info["animation_files"]) == 0:
            continue

        filename = file_info["filename"]
        print(f"Working with {filename}...")

        for animation_filename in file_info["animation_files"]:
            try:
                gltf = build_combined_gltf(
                    input_directory / filename, input_directory / animation_filename
                )
            except AnimationNotFoundException:
                print(f"No animation in the file {animation_filename!r}. File Skipped!")
                continue

            output_filepath = output_directory / animation_filename
            gltf.write(output_filepath)

            print(f' - Combined! Saved to the "{output_filepath}".')

    print("Done!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit(0)
