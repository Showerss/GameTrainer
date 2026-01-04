"""
ConfigLoader - Loads game profile configurations

Teacher Note: Each game has its own "profile" folder with configuration files:
    - regions.yaml: Where UI elements appear on screen
    - (future) rules.yaml: Decision rules
    - (future) templates/: Images for template matching

This module handles loading and parsing these YAML files.
"""

import os
from typing import Dict, Any, Optional

# Teacher Note: PyYAML is the standard library for reading YAML files in Python
# YAML is nicer than JSON for config files because it supports comments
import yaml


class ConfigLoader:
    """
    Loads configuration files from a game profile.

    Usage:
        loader = ConfigLoader("profiles/stardew_valley")
        regions = loader.load_regions()
        print(regions["energy_bar"])
    """

    def __init__(self, profile_path: str):
        """
        Initialize with a path to a game profile directory.

        Args:
            profile_path: Path to the profile folder (e.g., "profiles/stardew_valley")
        """
        self.profile_path = profile_path

        # Validate the path exists
        if not os.path.isdir(profile_path):
            print(f"Warning: Profile path does not exist: {profile_path}")

    def load_regions(self) -> Dict[str, Any]:
        """
        Load UI region definitions from regions.yaml.

        Returns:
            Dictionary of region definitions, or empty dict if file not found

        Teacher Note: Regions define WHERE on the screen each UI element appears.
        The vision components use these to know where to look for health bars, etc.
        """
        regions_path = os.path.join(self.profile_path, "regions.yaml")
        return self._load_yaml(regions_path)

    def get_region(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific region by name.

        Args:
            name: Name of the region (e.g., "energy_bar", "health_bar")

        Returns:
            Region dictionary or None if not found
        """
        regions = self.load_regions()
        ui_regions = regions.get("ui_regions", {})
        return ui_regions.get(name)

    def _load_yaml(self, path: str) -> Dict[str, Any]:
        """
        Load a YAML file and return its contents.

        Args:
            path: Full path to the YAML file

        Returns:
            Parsed YAML as dictionary, or empty dict if error
        """
        if not os.path.isfile(path):
            print(f"Config file not found: {path}")
            return {}

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data if data else {}
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file {path}: {e}")
            return {}
        except Exception as e:
            print(f"Error reading config file {path}: {e}")
            return {}

    @property
    def profile_name(self) -> str:
        """Get the profile name (folder name)."""
        return os.path.basename(self.profile_path)
