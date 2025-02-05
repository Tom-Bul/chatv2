"""
Plugin system implementation.
Provides functionality for loading and managing plugins.
"""

import importlib
import importlib.util
import os
import sys
from typing import Any, Dict, List, Optional, Type
from pathlib import Path

from .abstractions.base import IPlugin, IExtension, PluginManager
from .event_system import publish_event, GameStateEvent

class Plugin(IPlugin):
    """Base class for plugins."""
    def __init__(self, name: str, version: str):
        self._name = name
        self._version = version
        self._extensions: List[IExtension] = []
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def version(self) -> str:
        return self._version
    
    def initialize(self) -> None:
        """Initialize the plugin."""
        pass
    
    def get_extensions(self) -> List[IExtension]:
        """Get all extensions provided by this plugin."""
        return self._extensions
    
    def register_extension(self, extension: IExtension) -> None:
        """Register a new extension."""
        self._extensions.append(extension)

class Extension(IExtension):
    """Base class for extensions."""
    def __init__(self, point_id: str):
        self._point_id = point_id
    
    @property
    def point_id(self) -> str:
        return self._point_id
    
    def initialize(self) -> None:
        """Initialize the extension."""
        pass

class PluginLoader:
    """Handles loading plugins from files and directories."""
    @staticmethod
    def load_plugin_from_path(path: Path) -> Optional[IPlugin]:
        """Load a plugin from a Python file or package."""
        try:
            if path.is_file() and path.suffix == '.py':
                return PluginLoader._load_from_file(path)
            elif path.is_dir() and (path / '__init__.py').exists():
                return PluginLoader._load_from_directory(path)
            return None
        except Exception as e:
            publish_event(GameStateEvent(
                action="plugin_load_error",
                state_type="plugin_loader",
                details={
                    "path": str(path),
                    "error": str(e)
                }
            ))
            return None
    
    @staticmethod
    def _load_from_file(path: Path) -> Optional[IPlugin]:
        """Load a plugin from a single Python file."""
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            return None
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[path.stem] = module
        spec.loader.exec_module(module)
        
        # Look for Plugin class in the module
        for item_name in dir(module):
            item = getattr(module, item_name)
            if (isinstance(item, type) and 
                issubclass(item, Plugin) and 
                item is not Plugin):
                return item()
        return None
    
    @staticmethod
    def _load_from_directory(path: Path) -> Optional[IPlugin]:
        """Load a plugin from a directory containing __init__.py."""
        sys.path.insert(0, str(path.parent))
        try:
            module = importlib.import_module(path.name)
            # Look for Plugin class in the module
            for item_name in dir(module):
                item = getattr(module, item_name)
                if (isinstance(item, type) and 
                    issubclass(item, Plugin) and 
                    item is not Plugin):
                    return item()
        finally:
            sys.path.pop(0)
        return None

class GamePluginManager(PluginManager):
    """Game-specific plugin manager implementation."""
    def __init__(self):
        super().__init__()
        self._extension_points: Dict[str, Type[IExtension]] = {}
    
    def register_extension_point(self, point_id: str, extension_type: Type[IExtension]) -> None:
        """Register a new extension point type."""
        self._extension_points[point_id] = extension_type
        publish_event(GameStateEvent(
            action="register_extension_point",
            state_type="plugin_manager",
            details={"point_id": point_id}
        ))
    
    def load_plugins_from_directory(self, directory: Path) -> None:
        """Load all plugins from a directory."""
        if not directory.exists() or not directory.is_dir():
            return
        
        for item in directory.iterdir():
            plugin = PluginLoader.load_plugin_from_path(item)
            if plugin is not None:
                self.register_plugin(plugin)
                publish_event(GameStateEvent(
                    action="load_plugin",
                    state_type="plugin_manager",
                    details={
                        "name": plugin.name,
                        "version": plugin.version
                    }
                ))
    
    def get_extension_point_type(self, point_id: str) -> Optional[Type[IExtension]]:
        """Get the type for an extension point."""
        return self._extension_points.get(point_id)

# Global plugin manager instance
plugin_manager = GamePluginManager()

def load_plugins(directory: str) -> None:
    """Load plugins from a directory using the global plugin manager."""
    plugin_manager.load_plugins_from_directory(Path(directory))

def register_extension_point(point_id: str, extension_type: Type[IExtension]) -> None:
    """Register a new extension point type in the global plugin manager."""
    plugin_manager.register_extension_point(point_id, extension_type)

def get_extensions(point_id: str) -> List[IExtension]:
    """Get all extensions for a specific point from the global plugin manager."""
    return plugin_manager.get_extensions(point_id) 