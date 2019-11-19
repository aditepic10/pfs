import logging

from core.core import Core
from helpers.exceptions import ModuleNotFoundError


class Submodule:
    """
    Abstract class for all submodule, regardless of job
    """
    def __init__(self, name: str, core: Core, config: dict):
        """
        Instantiates a new Submodule instance
        :param name: name of submodule
        :param config: dictionary of configuration data
        """
        self.name = name
        self.core = core
        self.config = config
        self.logger = logging.getLogger(self.name)
        self.modules = dict()
        self.processes = dict()

    def start(self) -> None:
        """
        Iterates through self.processes and starts all processes.
        This method is meant to be overridden
        """

        for process in self.processes:
            self.processes[process].start()

    def enter_low_power_mode(self) -> None:
        """
        Immediately puts the submodule into a low power state. Different for each submodule.
        It is safe to assume that if this method is called, the previous state was NORMAL_MODE
        """
        for process in self.processes:
            self.processes[process].pause()

    def enter_normal_mode(self) -> None:
        """
        Immediately puts the submodule into a normal power state. Different for each submodule.
        It is safe to assume that if this method is called, the previous state was LOW_POWER_MODE
        :return:
        """
        for process in self.processes:
            self.processes[process].resume()

    def set_modules(self, dependencies: dict) -> None:
        """
        Accessor method for self.modules. self.modules shall be populated will any dependencies a submodule needs
        :param dependencies: Dictionary of references to other submodules that are required by the submodule
        :return: None
        """
        self.modules = dependencies

    def has_module(self, module_name: str) -> bool:
        """
        Returns True if module_name is in self.modules and its value is not None
        :param module_name: name of dependency module
        :return: bool
        """
        return module_name in self.modules and self.modules[module_name] is not None

    def get_module_or_raise_error(self, module_name: str):
        """
        Tries to access a reference to a dependency module and throws a RuntimeError otherwise
        :param module_name: name of dependency module
        :return: Reference to dependency module or None with RuntimeError raised
        """
        if self.has_module(module_name):
            return self.modules[module_name]
        else:
            err = ModuleNotFoundError(self, module_name)
            self.logger.error(str(err))
            raise err
    
    def __str__(self):
        return f"Submodule: {self.name()}"
