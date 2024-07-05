"""mailAttachmentPrinter printer"""
from os import remove,path
from sys import exit,stderr

from cups import setServer,Connection
from .config import get_config,LOGGER

CONFIGURATION = get_config()
setServer(CONFIGURATION['printer']['server'])

def __print_file(_file, printer, description=""):
    """print file"""
    conn = Connection()
    conn.printFile(printer, _file, description, {})

def try_connection():
    """try cups connection"""
    LOGGER.debug("Testing connection to cups printer server")
    try:
        conn = Connection()
        conn.getPrinters()
    except RuntimeError:
        LOGGER.critical("Error while connecting to cups printer server!")
        print("Error while connecting to cups printer server!", file=stderr)
        exit(-1)

def get_printers():
    """list available printers"""
    LOGGER.debug("Get available printers")
    printers = []
    for printer in Connection().getPrinters():
        printers.append(printer)
    LOGGER.debug("Available printers: %s",printers)
    return printers

def print_pdf(pdf_bytes, printer):
    """print pdf"""
    temporary_file_path = "/tmp/tmp.pdf"
    # remove temporary file
    if path.exists(temporary_file_path):
        remove(temporary_file_path)
    with open(temporary_file_path, 'bw') as tmp_file:
        tmp_file.write(pdf_bytes)
        LOGGER.debug("Printing file '%s' on Printer '%s'", temporary_file_path, printer)
        __print_file(temporary_file_path, printer)
        remove(temporary_file_path)  # remove temporary file
