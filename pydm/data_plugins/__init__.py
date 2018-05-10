"""
Loads all the data plugins available at the given PYDM_DATA_PLUGINS_PATH
environment variable and subfolders that follows the *_plugin.py and have
classes that inherits from the pydm.data_plugins.PyDMPlugin class.
"""
import os
import sys
import inspect
import logging
import imp
import uuid
from .plugin import PyDMPlugin

logger = logging.getLogger(__name__)
plugin_modules = {}


def add_plugin(plugin):
    """
    Add a PyDM plugin to the global registry of protocol vs. plugins

    Parameters
    ----------
    plugin: PyDMPlugin
    """
    # Warn users if we are overwriting a protocol which already has a plugin
    if plugin.protocol in plugin_modules:
        logger.warning("Replacing %s plugin with %s for use with protocol %s",
                       plugin, plugin_modules[plugin.protocol],
                       plugin.protocol)
    plugin_modules[plugin.protocol] = plugin


def load_plugins_from_path(locations, token):
    """
    Load plugins from file locations that match a specific token


    Parameters
    ----------
    locations: list
        List of file locations

    token : str
        Phrase that must match the end of the filename for it to be checked for
        PyDMPlugins

    Returns
    -------
    plugins: dict
        Dictionary of plugins
    """
    added_plugins = dict()
    for loc in locations:
        for root, _, files in os.walk(loc):
            if root.split(os.path.sep)[-1].startswith("__"):
                continue

            logger.info("Looking for PyDM Data Plugins at: {}".format(root))
            for name in files:
                if name.endswith(DATA_PLUGIN_TOKEN):
                    try:
                        logger.info("\tTrying to load {}...".format(name))
                        sys.path.append(root)
                        temp_name = str(uuid.uuid4())
                        module = imp.load_source(temp_name,
                                                 os.path.join(root, name))
                    except Exception as e:
                        logger.exception("Unable to import plugin file {}."
                                         "This plugin will be skipped."
                                         "The exception raised was: {}",
                                         name, e)
                    classes = [obj for name, obj in inspect.getmembers(module)
                               if (inspect.isclass(obj)
                                   and issubclass(obj, PyDMPlugin)
                                   and obj is not PyDMPlugin)]
                    # De-duplicate classes.
                    classes = list(set(classes))
                    if len(classes) == 0:
                        continue
                    if len(classes) > 1:
                        logger.warning("More than one PyDMPlugin subclass "
                                       "in file {}. The first occurrence "
                                       "(in alphabetical order) will be "
                                       "opened: {}", name, classes[0].__name__)
                    plugin = classes[0]
                    if plugin.protocol is not None:
                        if plugin_modules.get(plugin.protocol) != plugin:
                            logger.warning("More than one plugin is "
                                           "attempting to register the %s "
                                           "protocol. Which plugin will get "
                                           "called to handle this protocol "
                                           "is undefined.", plugin.protocol)
                        # Add to global plugin list
                        add_plugin(plugin)
                        # Add to return dictionary of added plugins
                        added_plugins[plugin.protocol] = plugin
    return added_plugins


# Load the data plugins from PYDM_DATA_PLUGINS_PATH
logger.info("*"*80)
logger.info("* Loading PyDM Data Plugins")
logger.info("*"*80)

DATA_PLUGIN_TOKEN = "_plugin.py"
path = os.getenv("PYDM_DATA_PLUGINS_PATH", None)
if path is None:
    locations = []
else:
    locations = path.split(os.pathsep)

# Ensure that we first visit the local data_plugins location
plugin_dir = os.path.dirname(os.path.realpath(__file__))
locations.insert(0, plugin_dir)

load_plugins_from_path(locations, DATA_PLUGIN_TOKEN)
