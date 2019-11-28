import re

from functools import partial

to_snake = partial(re.compile(r'([a-z0-9])([A-Z])').sub, r'\1_\2')
