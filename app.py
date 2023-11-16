from viewer import Viewer

class Application:
    _instance = None

    def __new__(cls, path):
        if not cls._instance:
            cls._instance = super(Application, cls).__new__(cls)
            cls._instance.path = path
        return cls._instance

    def __init__(self, project_dir):
        self.viewer = Viewer(project_dir)

    @classmethod
    def create_application(cls, project_dir):
        return cls(project_dir)
