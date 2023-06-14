from pathlib import Path

from gltf_combiner import build_combined_gltf


RESOURCES_PATH = Path("../test/resources")


def main() -> None:
    gltf = build_combined_gltf(RESOURCES_PATH / "maisie_geo.glb", RESOURCES_PATH / "maisie_win.glb")

    filepath = RESOURCES_PATH / "new.glb"
    gltf.write(filepath)

    print(f'Done! Saved to the "{filepath}".')


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit(0)
