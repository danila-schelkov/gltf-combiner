import os
import re
from pathlib import Path

from gltf_combiner import build_combined_gltf
from gltf_combiner.gltf.exceptions import AnimationNotFoundException

RESOURCES_PATH = Path("resources")
COMBINED_PATH = Path("combined")


def _collect_files_info(input_directory: Path, extension="glb") -> list:
    files = [
        {"filename": file, "animation_files": []}
        for file in os.listdir(input_directory)
        if os.path.isfile(input_directory / file)
    ]

    animations = []

    for file_index, file in enumerate(files):
        file = files[file_index]
        filename = file["filename"]

        if filename in animations:
            continue

        basename = os.path.splitext(filename)[0]

        if basename.endswith("_geo"):
            pattern = re.compile(rf"{basename[:-4]}.*")
            matches = list(filter(pattern.match, os.listdir(input_directory)))
            matches.remove(filename)

            for match in matches:
                match_basename = os.path.splitext(match)[0]

                if match_basename.endswith("_geo"):
                    pattern = re.compile(f"{match_basename[:-4]}.*(?!_geo).{extension}")
                    another_matches = list(
                        filter(pattern.match, os.listdir(input_directory))
                    )
                    matches = [
                        animation
                        for animation in matches
                        if animation not in another_matches
                    ]

            if len(matches) >= 1:
                animations.extend(matches)

                files[file_index]["animation_files"] = matches

    files = [file for file in files if file["filename"] not in animations]

    return files


def main() -> None:
    input_directory = RESOURCES_PATH
    output_directory = COMBINED_PATH
    os.makedirs(input_directory, exist_ok=True)
    os.makedirs(output_directory, exist_ok=True)

    collected_files = _collect_files_info(input_directory)
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
