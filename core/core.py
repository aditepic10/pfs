import logging
import os
import time

from functools import partial
from threading import Timer
from yaml import safe_load

from core.processes import power_watchdog, is_first_boot

from helpers import to_snake
from helpers.mode import Mode
from helpers.power import Power
from helpers.threadhandler import ThreadHandler

from submodules.antenna_deployer import AntennaDeployer
from submodules.command_ingest import CommandIngest
from submodules.eps import EPS
from submodules.radios.aprs import APRS
from submodules.radios.iridium import Iridium
from submodules.telemetry import Telemetry


class Core:

    def __init__(self):
        self.config = {'core': {'modules': {'A': ['eps', 'command_ingest'], 'B': ['antenna_deployer'], 'C': ['aprs', 'iridium', 'telemetry']}, 'dump_interval': 3600, 'sleep_interval': 1800}, 'antenna_deployer': {'depends_on': ['telemetry'], 'ANT_1': 0, 'ANT_2': 1, 'ANT_3': 2, 'ANT_4': 3}, 'aprs': {'depends_on': ['telemetry'], 'serial_port': '/dev/ttyUSB0', 'telem_timeout': 70, 'message_spacing': 1}, 'command_ingest': {'depends_on': ['antenna_deployer', 'aprs', 'eps', 'iridium', 'telemetry']}, 'eps': {'depends_on': ['telemetry'], 'looptime': 20}, 'iridium': {'depends_on': ['telemetry'], 'serial_port': '/dev/ttyUSB0'}, 'telemetry': {'depends_on': ['command_ingest'], 'buffer_size': 100, 'max_packet_size': 170}}

        self.logger = logging.getLogger(to_snake(Core.__name__))
        self.state = Mode.LOW_POWER

        self.submodules = {
            to_snake(submodule.__name__).lower(): submodule(config=self.config)
            for submodule in [AntennaDeployer, APRS, CommandIngest, EPS, Iridium, Telemetry]
        }

        self.populate_dependencies()
        self.processes = {
            "power_monitor": ThreadHandler(
                target=partial(power_watchdog, core=self, eps=self.submodules['eps']),
                name="power_monitor",
                parent_logger=self.logger
            ),
            "telemetry_dump": Timer(
                interval=self.config['core']['dump_interval'],
                function=partial(self.submodules["telemetry"].dump)
            )
        }
        self.logger.info("Initialized")

    def populate_dependencies(self) -> None:
        """
        Iterates through configuration data dictionary and sets each submodule's self.modules dictionary
        with a dictionary that contains references to all the other submodules listed in the first 
        submodule's depends_on key
        """
        for submodule in self.submodules:
            if hasattr(self.submodules[submodule], 'set_modules'):
                self.submodules[submodule].set_modules({
                    dependency: self.submodules[dependency]
                    for dependency in self.config[submodule]['depends_on']
                })

    def get_config(self) -> dict:
        """Returns the configuration data from config_*.yml as a list"""
        return self.config

    def get_state(self) -> Mode:
        return self.state

    def enter_normal_mode(self, reason: str = '') -> None:
        """
        Enter normal power mode.
        :param reason: Reason for entering normal mode.
        """
        self.logger.warning(
            f"Entering normal mode{'  Reason: ' if reason else ''}{reason if reason else ''}")
        self.state = Mode.NORMAL
        for submodule in self.submodules:
            if hasattr(self.submodules[submodule], 'enter_normal_mode'):
                self.submodules[submodule].enter_normal_mode()

    def enter_low_power_mode(self, reason: str = '') -> None:
        """
        Enter low power mode.
        :param reason: Reason for entering low power mode.
        """
        self.logger.warning(
            f"Entering low power mode{'  Reason: ' if reason else ''}{reason if reason else ''}")
        self.state = Mode.LOW_POWER
        for submodule in self.submodules:
            if hasattr(self.submodules[submodule], 'enter_low_power_mode'):
                self.submodules[submodule].enter_low_power_mode()

    def request(self, module_name: str):
        """
        Returns a reference to a specified module if specified module is present
        @param module_name: name of module requested
        """
        return self.submodules[module_name] if module_name in self.submodules.keys() else False

    def start(self) -> None:
        """
        Runs the startup process for core
        """
        for submodule in self.config['core']['modules']['A']:
            if hasattr(self.submodules[submodule], 'start'):
                self.submodules[submodule].start()

        if is_first_boot():
            time.sleep(self.config['core']['sleep_interval'])

        for submodule in self.config['core']['modules']['B']:
            if hasattr(self.submodules[submodule], 'start'):
                self.submodules[submodule].start()
        
        while self.submodules['eps'].get_battery_bus_volts() < Power.STARTUP.value:
            time.sleep(1)
        self.mode = Mode.NORMAL

        for submodule in self.config['core']['modules']['C']:
            if hasattr(self.submodules[submodule], 'start'):
                self.submodules[submodule].start()

        for process in self.processes:
            self.processes[process].start()

        while True:
            time.sleep(1) # Keep main thread alive so that child threads do not terminate
