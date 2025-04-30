import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from gltf_combiner import build_combined_gltf
from gltf_combiner.gltf.exceptions import (
    AnimationNotFoundException,
    AllAnimationChannelsDeletedException,
)

RESOURCES_PATH = Path("resources")
COMBINED_PATH = Path("combined")


@dataclass
class AnimatedFile:
    filename: str
    animation_files: list[str] = field(default_factory=list)


def _collect_files_info(input_directory: Path, extension="glb") -> list[AnimatedFile]:
    """
    Collects info about models and their animations if model name ends with `_geo`
    and animation names end with `_anim`, where `anim` is an animation name.
    """

    animated_files = [
        AnimatedFile(file)
        for file in os.listdir(input_directory)
        if os.path.isfile(input_directory / file)
    ]

    animations = []

    for file_index, file in enumerate(animated_files):
        filename = file.filename

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
                    pattern = re.compile(
                        f"{match_basename[:-4]}.*(?!_geo)\.{extension}"
                    )
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

                file.animation_files.extend(matches)

    animated_files = [
        file for file in animated_files if file.filename not in animations
    ]

    return animated_files


def main() -> None:
    input_directory = RESOURCES_PATH
    output_directory = COMBINED_PATH
    os.makedirs(input_directory, exist_ok=True)
    os.makedirs(output_directory, exist_ok=True)

    collected_files = _collect_files_info(input_directory)
    for file_info in collected_files:
        if len(file_info.animation_files) == 0:
            continue

        print(f"Working with {file_info.filename}...")

        for animation_filename in file_info.animation_files:
            try:
                gltf = build_combined_gltf(
                    input_directory / file_info.filename,
                    input_directory / animation_filename,
                    fix_texcoords=True,
                )
            except AnimationNotFoundException | AllAnimationChannelsDeletedException:
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
