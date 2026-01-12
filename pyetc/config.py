import os


#
class Config:
    def __init__(self, project_dir: str = "."):
        self._project_dir = os.path.abspath(project_dir)

    @property
    def project_dir(self):
        return self._project_dir
