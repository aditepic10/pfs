import functools
import logging
import threading
import time

from core import Core
from helpers.exceptions import ModuleNotFoundError


class ThreadHandler:
    def __init__(self, core: Core, target: callable, name: str = None, parent_logger=logging, interval: int = 3,
                 suppress_out: bool = False, auto_restart: bool = True, daemon: bool = False):
        """
        Initialize a ThreadHandler.

        :param target: The child function to run, should be either a functools.partial or lambda.
        :param name: The name of the thread; default is name of function or pointer location.
        :param parent_logger: A logging object (ex. GPS); default 'root'.
        :param interval: Amount of time between checking the status of the child function; default 3s.
        :param suppress_out: Suppresses the logging of messages; default False.
        :param auto_restart: Whether or not to automatically restart the thread.
        :param daemon: Set True to stop thread when main thread terminates
        """

        self.target = target

        if name is None:
            if type(target) == functools.partial:
                self.name = target.func.__name__
            # TODO figure out why function is not defined
            elif type(target) is type(lambda x: x):
                self.name = target.__name__
            else:
                self.name = "thread_" + str(id(self))
        else:
            self.name = name

        self.parent_logger = parent_logger
        self.interval = interval
        self.suppress_out = suppress_out
        self.auto_restart = auto_restart
        self.is_active = True
        self.is_alive = False
        self.daemon = daemon
        self.core = core

    def start(self):
        """
        Start the ThreadHandler. This function actually starts a threading.Thread, with the run() method as the target.
        """
        threading.Thread(target=self.run, name=self.name, daemon=self.daemon).start()

    def run(self):
        while True:
            if self.is_active:
                if not self.suppress_out:
                    self.parent_logger.info("'%s' thread started" % self.name)
                try:
                    self.target()
                except ModuleNotFoundError as m:
                    self.core.reset_module(m.submodule, m.missing)        
                except BaseException as e:            
                    if not self.suppress_out:
                        self.parent_logger.exception(
                            str(e) + ", restarting '%s'" % self.name)
                    if not self.auto_restart:
                        self.is_active = False
                else:
                    if not self.suppress_out:
                        self.parent_logger.info(
                            "Bad thread, restarting '%s'" % self.name)
                    if not self.auto_restart:
                        self.is_active = False
            time.sleep(self.interval)

    def resume(self):
        """
        Resume the ThreadHandler.
        """
        if not self.suppress_out:
            self.parent_logger.info("'%s' thread resumed" % self.name)
        if not self.auto_restart:
            self.is_active = True

    def pause(self):
        """
        Pause the ThreadHandler.
        """
        if not self.suppress_out:
            self.parent_logger.info("'%s' thread paused" % self.name)
        if not self.auto_restart:
            self.is_active = False