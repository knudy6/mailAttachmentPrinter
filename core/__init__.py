"""mailAttachmentPrinter core"""
from schedule import every,run_pending
from sys import exit
from time import sleep
from json import dumps

from .config import get_config,LOGGER
from .printer import get_printers,try_connection as printer_try_connection
from .reader import read_email,try_connection as reader_try_connection

def main():
    """main"""
    configuration = get_config()

    # check if connection to cups is possible
    printer_try_connection()

    # check if connection to imap server is possible
    reader_try_connection()

    # check if printer name is empty
    printers = get_printers()
    if configuration['printer']['name'] == "" or configuration['printer']['name'] not in printers:
        LOGGER.critical("Error with Printers!")
        print('Please set up a printer_name from the available names:')
        print(printers)
        print('Please set the \'$.printer.name\' in config.json or the environment variable: \'PRINTER_NAME\'')
        exit(-1)
    LOGGER.debug("Configured printer in cups printer server list")

    # print config
    LOGGER.info("Running with the following configuration:")
    print_configuration = configuration.copy()
    print_configuration['imap']['credentials']['password'] = "******"
    LOGGER.info(dumps(print_configuration, indent=2))

    # run main program
    every(int(configuration['scan_interval'])).seconds.do(read_email)

    LOGGER.info('MailPrinter is now running...')

    while True:
        run_pending()
        sleep(1)
