"""mailAttachmentPrinter config"""
from json import load
from os import environ,mkdir
from os.path import exists,dirname,realpath,isdir,join
from pytz import timezone
from sys import exit,stderr
from logging import getLogger,INFO,StreamHandler,Formatter

TRUE_VALUES = ['true', '1', 'y', 'yes']

APP_DIRECTORY = dirname(dirname(realpath(__file__)))
CONFIG_DIRECTORY = join(APP_DIRECTORY, "config")
CONFIG_FILE = join(CONFIG_DIRECTORY, "config.json")
TIDES_DELIMITER = "#"
TIDES_DIRECTORY = join(APP_DIRECTORY, "tides")
TIDES_ENCODING = "iso 8859-1"
TIDES_TIMEZONE = timezone("Etc/GMT-1")
TMP_DIRECTORY = join(APP_DIRECTORY, "tmp")

_LOGGER_HANDLER = StreamHandler()
_LOGGER_HANDLER.setFormatter(Formatter("%(asctime)s - %(levelname)s - %(message)s"))
LOGGER = getLogger('mailAttachmentPrinter')
LOGGER.addHandler(_LOGGER_HANDLER)
LOGGER.setLevel(INFO)

## DEBUG
PRINTER_ENABLE = True

def __load_config_file() -> dict:
    """load config from file"""
    # check if file exists
    if exists(CONFIG_FILE):
        # load config from file
        config_file = open(CONFIG_FILE, 'r')
        try:
            config = load(config_file)

            # Check if config and values are in proper format
            assert config['imap']['credentials']['password'] != "" and type(config['imap']['credentials']['password']) == str, "'$.imap.credentials.password' is not a string or empty."
            assert config['imap']['credentials']['username'] != "" and type(config['imap']['credentials']['username']) == str, "'$.imap.credentials.username' is not a string or empty."
            assert type(config['imap']['force_ssl']) == bool, "'$.printer.name' is not a Bool."
            assert type(config['imap']['port']) == int, "'$.imap.port' is not a integer."
            assert config['imap']['server'] != "" and type(config['imap']['server']) == str, "'$.imap.server' is not a string or empty."
            assert type(config['printer']['name']) == str, "'$.printer.name' is not a string."
            assert config['printer']['server'] != "" and type(config['imap']['server']) == str, "'$.printer.server' is not a string or empty."
            assert type(config['scan_interval']) == int, "'$.scan_interval' is not a integer."
            assert type(config['tide']['enabled']) == bool, "'$.tide.enabled' is not a bool."
            if config['tide']['enabled']:
                assert config['tide']['stations'] != [] and type(config['tide']['stations']) == list, "'$.tide.stations' is not a list or empty."

            return config
        # give detailed error messages
        except AssertionError as exception:
            print('Invalid configuration detected!', file=stderr)
            print(exception, file=stderr)
            exit(-1)
        except KeyError as exception:
            print('Invalid configuration detected!', file=stderr)
            print("A Configuration entry could not be loaded. Please copy all configuration entries from", CONFIG_FILE + ".sample", file=stderr)
            print("Info: if '$.tide.enabled' is set to 'false' the entry '$.tide.stations' is not required", file=stderr)
            exit(-1)
        except Exception as exception:
            print(exception)
            print('Invalid configuration detected!', file=stderr)
            print("Could not load json config from file:", CONFIG_FILE, file=stderr)
            exit(-1)
    return {}

def __load_environment_variables() -> dict:
    """load config from environment variables"""
    try:
        # Check if required environment variables are set and in proper format
        assert environ.get("IMAP_CREDENTIALS_PASSWORD") != "" and environ.get("IMAP_CREDENTIALS_PASSWORD") != None, "Environment variable 'IMAP_CREDENTIALS_PASSWORD' is not a set or empty."
        assert environ.get("IMAP_CREDENTIALS_USERNAME") != "" and environ.get("IMAP_CREDENTIALS_USERNAME") != None, "Environment variable 'IMAP_CREDENTIALS_USERNAME' is not a set or empty."
        assert environ.get("IMAP_SERVER") != "" and environ.get("IMAP_SERVER") != None, "Environment variable 'IMAP_SERVER' is not a set or empty."
        assert environ.get("PRINTER_SERVER") != "" and environ.get("PRINTER_SERVER") != None, "Environment variable 'PRINTER_SERVER' is not a set or empty."
        if environ.get("TIDE_ENABLED", default="False").lower() in TRUE_VALUES:
            assert environ.get("TIDE_STATIONS") != "" and environ.get("TIDE_STATIONS") != None, "Environment variable 'TIDE_STATIONS' is not a set or empty."
    # give detailed error messages
    except AssertionError as exception:
        print('Invalid configuration detected!', file=stderr)
        print(exception, file=stderr)
        exit(-1)

    config = {
        "imap": {
            "credentials": {
                "password": environ.get("IMAP_CREDENTIALS_PASSWORD"),
                "username": environ.get("IMAP_CREDENTIALS_USERNAME")
            },
            "force_ssl": environ.get("IMAP_FORCE_SSL", default="True").lower() in TRUE_VALUES,
            "port": int(environ.get("IMAP_PORT", default=993)),
            "server": environ.get("IMAP_SERVER")
        },
        "printer": {
            "name": environ.get("PRINTER_NAME", default=""),
            "server": environ.get("PRINTER_SERVER")
        },
        "scan_interval": int(environ.get("SCAN_INTERVAL", default=10)),
        "tide": {
            "enabled": environ.get("TIDE_ENABLED", default="False").lower() in TRUE_VALUES
        }
    }

    if environ.get("IMAP_FROM_ADDRESS") != None:
        config["imap"]["from_address"] = environ.get("IMAP_FROM_ADDRESS")
    if environ.get("LOG_LEVEL") != None:
        config["log"] = {}
        config["log"]["level"] = environ.get("LOG_LEVEL")
    if config["tide"]["enabled"]:
        config["tide"]["stations"] = environ.get("TIDE_STATIONS").split(",")

    return config

def _set_log_level(config) -> None:
    """Set Log Level"""
    try:
        level = config['log']['level']
    except KeyError:
        level = INFO
    LOGGER.setLevel(level)

def __check_directories(config) -> None:
    """check directories and create missing"""
    if not isdir(TMP_DIRECTORY):
        if exists(TMP_DIRECTORY):
            LOGGER.critical("Path %s exists, but is not a directory", TMP_DIRECTORY)
            exit(-1)
        mkdir(TMP_DIRECTORY)
    if config["tide"]["enabled"]:
        if not isdir(TIDES_DIRECTORY):
            if exists(TIDES_DIRECTORY):
                LOGGER.critical("Path %s exists, but is not a directory", TIDES_DIRECTORY)
                exit(-1)
            mkdir(TIDES_DIRECTORY)

def get_config() -> dict:
    """return config"""
    # load config from file
    config = __load_config_file()
    # load config from environment variables if config file fails
    if config == {}:
        config = __load_environment_variables()

    _set_log_level(config)
    __check_directories(config)

    return config
