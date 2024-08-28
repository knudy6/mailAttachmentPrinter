"""mailAttachmentPrinter core"""
from copy import deepcopy
from schedule import every,run_pending
from sys import exit
from time import sleep
from json import dumps

from .config import get_config,LOGGER
from .printer import get_printers,try_connection as printer_try_connection,set_server as printer_set_server
from .reader import read_email,try_connection as reader_try_connection

def main():
    """main"""
    configuration = get_config()

    # check if connection to cups is possible
    printer_set_server(configuration)
    printer_try_connection()

    # check if connection to imap server is possible
    reader_try_connection(configuration)

    # check if printer name is empty
    printers = get_printers()
    if configuration['printer']['name'] == "" or configuration['printer']['name'] not in printers:
        LOGGER.critical("Error with Printers!")
        print('Please set up a printer_name from the available names:')
        print(printers)
        print('Please set the \'$.printer.name\' in config.json or the environment variable: \'PRINTER_NAME\'')
        exit(-1)
    LOGGER.debug("Configured printer in cups printer server list")

    # check tide requirements if enabled
    if configuration["tide"]["enabled"]:
        from .tides import check_requirements
        check_requirements(configuration)

    # print config
    LOGGER.info("Running with the following configuration:")
    print_configuration = deepcopy(configuration)
    print_configuration['imap']['credentials']['password'] = "******"
    LOGGER.info(dumps(print_configuration, indent=2))

    # run main program
    every(int(configuration['scan_interval'])).seconds.do(lambda: read_email(configuration))

    LOGGER.info('MailPrinter is now running...')

    while True:
        run_pending()
        sleep(1)
