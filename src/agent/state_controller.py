from abc import ABC, abstractmethod

class BaseStateController(ABC):

    @abstractmethod
    def compute_state(self):
        pass

    @abstractmethod
    def udpate_state(self):
        pass