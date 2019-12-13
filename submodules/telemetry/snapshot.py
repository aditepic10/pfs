from time import time


class Snapshot:
    def __init__(self):
        self.metrics = {"TIME": time()}

    def add_metric(self, name, data):
        self.metrics[name] = data

    def create_message(self, name, keys):
        message = f"{name};"
        for key in keys:
            try:
                message += f"{self.metrics[key]};"
            except:
                message += ";"
        return message

    def get_beacon(self):
        beacon = self.create_message("BEACON", ["TIME"])
        return beacon

    def get_dump(self):
        dump = self.create_message("NEW_DUMP", ["TIME"])
        return dump
