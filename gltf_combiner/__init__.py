import os
import re
from pathlib import Path

from gltf_combiner.combiner import build_combined_gltf
from gltf.gltf import GlTF


def collect_files_info(input_directory: Path) -> list:
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
                    pattern = re.compile(f"{match_basename[:-4]}.*.{input_directory}")
                    another_matches = list(filter(pattern.match, os.listdir(input_directory)))
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
