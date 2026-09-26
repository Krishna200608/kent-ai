"""Configuration loading and path resolution utilities for Kent-AI."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


def get_project_root() -> Path:
    """Return the absolute path to the root directory of the repository.
    
    Traverses upward from this file until locating pyproject.toml or repertory.sqlite.
    """
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if (
            (parent / "pyproject.toml").is_file()
            or (parent / "data" / "raw" / "kent_public_edition").is_dir()
            or (parent / "kent_public_edition").is_dir()
        ):
            return parent
    return Path.cwd()


def load_yaml(filepath: Path | str) -> Dict[str, Any]:
    """Load and parse a YAML file safely.
    
    Args:
        filepath: Path to YAML configuration file.
        
    Returns:
        Dictionary representation of configuration.
        
    Raises:
        FileNotFoundError: If the specified file does not exist.
        yaml.YAMLError: If parsing fails.
    """
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        content = yaml.safe_load(f)
    return content or {}


def load_config(config_name: str) -> Dict[str, Any]:
    """Load a configuration file from the configs/ directory by name.
    
    Args:
        config_name: Name of config file with or without .yaml extension.
        
    Returns:
        Loaded configuration dictionary.
    """
    if not config_name.endswith(".yaml") and not config_name.endswith(".yml"):
        config_name = f"{config_name}.yaml"
    
    config_dir = get_project_root() / "configs"
    return load_yaml(config_dir / config_name)


def get_model_config(filepath: Optional[Path | str] = None) -> Dict[str, Any]:
    """Load ClinicalBERT model configuration."""
    if filepath:
        return load_yaml(filepath)
    return load_config("model.yaml")


def get_generation_config(filepath: Optional[Path | str] = None) -> Dict[str, Any]:
    """Load LLaMA case generation configuration."""
    if filepath:
        return load_yaml(filepath)
    return load_config("generation.yaml")


def get_chromadb_config(filepath: Optional[Path | str] = None) -> Dict[str, Any]:
    """Load ChromaDB vector store configuration."""
    if filepath:
        return load_yaml(filepath)
    return load_config("chromadb.yaml")


def get_chatbot_config(filepath: Optional[Path | str] = None) -> Dict[str, Any]:
    """Load conversational chatbot configuration."""
    if filepath:
        return load_yaml(filepath)
    return load_config("chatbot.yaml")


# Convenient aliases
load_model_config = get_model_config
load_generation_config = get_generation_config
load_chromadb_config = get_chromadb_config
load_chatbot_config = get_chatbot_config

