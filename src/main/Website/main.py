from os.path import abspath, join

from FileTagServer.WEB.app import LocalPathConfig, RemotePathConfig
from FileTagServer.WEB.main import run

if __name__ == "__main__":
    local_pathing = LocalPathConfig("../../../web")
    db_path = abspath(join(__file__, r"../../local.db"))
    run(db_path, local_pathing, host="localhost", port=80)
