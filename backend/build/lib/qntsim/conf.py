import os

import pkg_resources

print(__name__, "HARE", os.getcwd())
# LOG_CONFIG_FILE = "/code/web/logging.ini"

LOG_CONFIG_FILE = pkg_resources.resource_filename(__name__, "logging.ini")
# LOG_CONFIG_FILE = "\\".join(list(os.path.split(os.path.dirname(os.path.abspath(__file__))))+["logging.ini"])
# LOG_CONFIG_FILE = "logging.ini"
print(__name__, f"Log configuration file path: {LOG_CONFIG_FILE}")
if not os.path.exists(LOG_CONFIG_FILE):
    raise ValueError("Log configuration file not found: {}".format(LOG_CONFIG_FILE))

# with open(LOG_CONFIG_FILE, 'r') as file:
#     print(file.read())

# dir_path = os.path.split(os.path.dirname(os.path.abspath(__file__)))
# print(dir_path[0].replace("\\", "..")[1:])
# print(os.path.split(os.path.dirname(os.path.abspath(__file__))))
# print("\\".join(list(os.path.split(os.path.dirname(os.path.abspath(__file__))))+["logging.ini"]))