from submodules import aprs
from submodules import iridium

default_radio: str = "aprs"



def send(message: str, radio=None):
    """
    Send a message back to the groundstation.
    :param message: Message to send to the radio.
    :param radio: Radio to which to send the message. If `None`, send to the default radio.
    """
    if radio is None:
        radio = default_radio
    if radio == "aprs":
        aprs.send(message)
    if radio == "iridium":
        iridium.send(message)
