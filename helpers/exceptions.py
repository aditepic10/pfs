from submodules import Submodule

class ModuleNotFoundError(Exception):

    def __init__(self, submodule: Submodule, dependency: str):
        super().__init__(f"{submodule} cannot access {dependency}")

        self.submodule = submodule
        self.missing = dependency

    def get_submodule(self):
        return self.submodule

    def get_missing(self):
        return self.missing

    def __str__(self):
        return f"{self.submodule} cannot access {self.missing}"% 