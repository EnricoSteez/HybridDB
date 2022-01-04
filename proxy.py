class Knowledge:
    def __init__(self) -> None:
        self.dictionary = dict()

    def isSafeToWrite(self, key) -> bool:
        if self.dictionary[key].location != 2:
            # 2 means that the item is in transfer during optimization
            return True
        else:
            return False


class Proxy:
    def __init__(self) -> None:
        self.knowledge = Knowledge()

    def write_callback(self, newValue, key=None):
        if key in self.knowledge:  # update
            if self.knowledge[key] != 3:  # can update
                ...
            else:
                # FREEZE
                ...
        else:  # insert
            ...

    def read_callback(key):
        ...
