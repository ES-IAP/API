from enum import Enum

class Status(str, Enum):
    TODO = "to-do"
    INPROGRESS = "in progress"
    DONE = "done"
