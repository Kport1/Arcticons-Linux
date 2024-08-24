#!/usr/bin/python3
"""Icon Search."""

# Example usage: python ./icon-search.py steam -v
from __future__ import annotations

import argparse
from configparser import ConfigParser
from pathlib import Path
from typing import NamedTuple

# Mapping of Icon Contexts to folder names
ICON_TYPES = {
    "Actions": "actions",
    "Applications": "apps",
    "Categories": "categories",
    "Devices": "devices",
    "Emblems": "emblems",
    "Emotes": "emotes",
    "MimeTypes": "mimetypes",
    "Places": "places",
    "Status": "status",
}


class IconDirEntry(NamedTuple):
    """An icon directory entry."""

    directory: Path
    icon_type: str


def search_icons(appname: str) -> dict[str, list[Path]]:
    """Search for icons containing the specified appname."""

    # find all theme files
    theme_files = {
        *set(Path("/usr/share/icons").glob("*/index.theme")),
        *set(Path("~/.local/share/icons").expanduser().glob("*/index.theme")),
    }
    icon_directories: list[IconDirEntry] = []

    for theme_file in theme_files:
        theme_file_config = ConfigParser()
        if (
            str(theme_file) not in theme_file_config.read(theme_file)
            or "Icon Theme" not in theme_file_config
            or "Directories" not in theme_file_config["Icon Theme"]
        ):
            # Not an icon theme file
            continue

        # Parse all directories inside the theme file
        for directory in theme_file_config["Icon Theme"]["Directories"].split(","):
            dir_path = theme_file.parent / directory
            if (
                dir_path.is_dir()
                and not dir_path.is_symlink()  # The Papirus theme has symlinks from categories to apps, so each app would be a category as well
                and not dir_path.parent.is_symlink()
                and directory in theme_file_config
                and "Context" in theme_file_config[directory]
            ):
                icon_directories.append(
                    IconDirEntry(
                        directory=dir_path,
                        icon_type=theme_file_config[directory]["Context"],
                    ),
                )

    # Parse ~/.local/share/icons/hicolor, because it doesn't have a theme file
    icon_directories += [
        IconDirEntry(
            directory=folder,
            icon_type=([*ICON_TYPES.keys()][[*ICON_TYPES.values()].index(folder.name)]),
        )
        for folder in Path("~/.local/share/icons/hicolor").glob("*/*")
        if folder.is_dir()
    ]

    # Search in all directories for files with the appname in the filename
    entries: dict[str, list[Path]] = {}
    for folder in icon_directories:
        for file in folder.directory.glob(f"*{appname}*"):
            mapping_str = f"{ICON_TYPES[folder.icon_type]}/{file.stem}"
            if mapping_str.endswith("-symbolic"):
                mapping_str = mapping_str.removesuffix("-symbolic")
            if mapping_str in entries:
                entries[mapping_str].append(file)
            else:
                entries[mapping_str] = [file]
    return entries


if __name__ == "__main__":
    # Parse arguments from command line
    parser = argparse.ArgumentParser()
    parser.add_argument("appname", help="name of the app to search icons for")
    parser.add_argument(
        "-v",
        "--verbose",
        help="increase output verbosity",
        action="store_true",
    )
    args = parser.parse_args()

    entries = search_icons(args.appname)

    # Display results
    if args.verbose:
        for entry, entry_paths in sorted(entries.items()):
            print(entry + " found in:")
            for entry_path in entry_paths:
                print(f"\t{entry_path}")
    else:
        for entry in sorted(entries):
            print(f"{entry}")