from time import time


class Snapshot:
    def __init__(self, identifier):
        """
        Initializes a metrics snapshot with the time the metrics were collected
        :param identifier: the unique identifier number for the snapshot
        """
        self.identifier = identifier
        self.metrics = {"TIME": time()}

    def add_metric(self, name, data):
        """
        Assigns a metric to the metrics snapshot
        :param name: metric name
        :param data: metric contents
        :return: None
        """
        self.metrics[name] = data

    def create_message(self, name, keys):
        """
        Returns a message for telemetry to send through a radio
        :param name: the header for the message (e.g. `BEACON`)
        :param keys: the metric names to put into the message (in order)
        :return: str to send through a radio
        """
        message = f"{name};"
        for key in keys:
            try:
                message += f"{self.metrics[key]};"
            except KeyError:
                message += ";"
        return message

    def get_beacon(self):
        """
        Creates a beacon message to send through the radio.
        :return: str that represents the beacon information
        """
        beacon = self.create_message("BEACON", ["TIME"])
        return beacon

    def get_dump(self):
        """
        Creates a dump message for the specific snapshot
        :return: str that represents all the metrics in the snapshot
        """
        dump = self.create_message(f"{self.identifier}", ["TIME"])
        return dump
