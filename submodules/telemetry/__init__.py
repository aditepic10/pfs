import base64  # packet encoding
import logging  # logger
import time

from functools import partial  # thread
from threading import Lock  # packet locks
from time import sleep  # decide method
from collections import deque  # general, error, log queues

from submodules.submodule import Submodule
from .snapshot import Snapshot
from helpers.threadhandler import ThreadHandler  # threads
from helpers import error, log  # Log and error classes


class Telemetry(Submodule):
    def __init__(self, config):
        """
        Constructor method. Initializes variables
        :param config: Config variable passed in from core.
        """
        Submodule.__init__(self, name="telemetry", config=config)

        self.general_queue = deque()
        self.log_stack = deque()
        self.err_stack = deque()
        self.packet_lock = Lock()
        self.snapshots = []
        self.processes = {
            "telemetry-decide": ThreadHandler(
                target=partial(self.decide),
                name="telemetry-decide",
                parent_logger=self.logger,
                daemon=False,
            )
        }

    def enqueue(self, message) -> bool:
        """
        Enqueue a message onto the general queue, to be processed later by thread decide()
        :param message: The message to push onto general queue. Must be a log/error class
        or command (string - must begin with semicolon, see command_ingest's readme)
        :return True if a valid message was enqueued, false otherwise
        """
        if not (
            (
                type(message) is str and message[0:4] == "CMD$" and message[-1] == ";"
            )  # message is Command
            or type(message) is error.Error  # message is Error
            or type(message) is log.Log
        ):  # message is Log
            self.logger.error("Attempted to enqueue invalid message")
            return False
        with self.packet_lock:
            self.general_queue.append(message)  # append to general queue
            return True

    def dump(self, radio="aprs") -> bool:
        """
        Concatenates packets to fit in max_packet_size (defined in config) and send through the radio, removing the
        packets from the error and log stacks in the process
        :param radio: Radio to send telemetry through, either "aprs" or "iridium"
        :return True if anything was sent, false otherwise
        """
        squished_packets = ""
        success = False

        with self.packet_lock:
            dump = self.create_metrics_dump() + ";"
            while len(self.err_stack) > 0:
                # while there's stuff to pop off

                next_error_packet = str(self.err_stack[-1])
                dump += f";{next_error_packet}"

                success = True

            max_len = self.config["telemetry"]["max_packet_size"]
            messages = [
                squished_packets[i : i + max_len]
                for i in range(0, len(squished_packets), max_len)
            ]
            for message in messages:
                self.get_module_or_raise_error(radio).send(message)

        return success

    def clear_buffers(self) -> None:
        """
        Clear the telemetry buffers - clearing general_queue, the log, and error stacks.
        :return: None
        """
        with self.packet_lock:
            self.general_queue.clear()
            self.err_stack.clear()

    def decide(self) -> None:
        """
        A thread method to constantly check general_queue for messages and process them if there are any.
        :return: None
        """
        while True:
            if len(self.general_queue) != 0:
                with self.packet_lock:
                    message = self.general_queue.popleft()
                    if (
                        type(message) is str
                        and message[0:4] == "CMD$"
                        and message[-1] == ";"
                    ):
                        self.get_module_or_raise_error("command_ingest").enqueue(
                            message
                        )
                        # print("Running command_ingest.enqueue(" + message + ")")
                    elif type(message) is error.Error:
                        self.err_stack.append(message)
                    elif type(message) is log.Log:
                        self.log_stack.append(message)
                    else:  # Shouldn't execute (enqueue() should catch it) but here just in case
                        self.logger.error("Message prefix invalid.")
            sleep(1)

    def add_metric(self, name, data, append=False):
        """
        Any submodule can add their relevant metrics to the most recent data snapshot through the telemetry object
        :param name: the metric name
        :param data: the metric data
        :param append: add the data to the existing data
        :return: None
        """
        self.snapshots[-1].add_metric(name, data, append)

    def create_metrics_dump(self):
        """
        Creates a big message w/ up to the 100 most recent snapshots.
        :return: str
        """
        metrics_dump = ""
        snapshots = 0
        for index in range(len(self.snapshots) - 1, -1, -1):
            if snapshots == 100:
                return metrics_dump
            metrics_dump += self.snapshots[index].get_dump()
            snapshots += 1
        return metrics_dump

    def start_beacon(self):
        """
        Sends a beacon signal through APRS and create a new metrics Snapshot.
        :return: None
        """
        try:
            beacon = self.snapshots[-1].get_beacon()
            self.get_module_or_raise_error("aprs").send(beacon)
        except IndexError:
            pass

        self.snapshots.append(Snapshot(len(self.snapshots)))

    def heartbeat(self) -> None:
        """
        Send a heartbeat through Iridium.
        :return: None
        """
        self.get_module_or_raise_error("iridium").send(
            "TJREVERB ALIVE, {0}".format(time.time())
        )

    def enter_normal_mode(self) -> None:  # TODO: IMPLEMENT IN CYCLE 2
        """
        Enter normal mode.
        :return: None
        """
        pass

    def enter_low_power_mode(self) -> None:  # TODO: IMPLEMENT IN CYCLE 2
        """
        Enter low power mode.
        :return: None
        """
        pass
