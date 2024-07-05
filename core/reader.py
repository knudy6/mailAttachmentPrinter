"""mailAttachmentPrinter reader"""
from sys import exit,stderr
from imaplib import IMAP4,IMAP4_SSL
from email import message_from_bytes

from .printer import print_pdf
from .config import get_config,LOGGER

CONFIGURATION = get_config()

def try_connection():
    """try imap connection"""
    LOGGER.debug("Testing connection and authentifikation to imap server")

    if CONFIGURATION['imap']['force_ssl']:
        mail = IMAP4_SSL(CONFIGURATION['imap']['server'], CONFIGURATION['imap']['port'])
    else:
        mail = IMAP4(CONFIGURATION['imap']['server'], CONFIGURATION['imap']['port'])

    password = CONFIGURATION['imap']['credentials']['password']
    username = CONFIGURATION['imap']['credentials']['username']

    try:
        mail.login(username, password)
    except Exception as exception:
        LOGGER.critical("Error while connection to imap server!")
        print("Error while connection to imap server!", file=stderr)
        print(exception, file=stderr)
        exit(-1)

def read_email():
    """read mail from imap server"""
    LOGGER.info("Checking for emails")

    if CONFIGURATION['imap']['force_ssl']:
        mail = IMAP4_SSL(CONFIGURATION['imap']['server'], CONFIGURATION['imap']['port'])
    else:
        mail = IMAP4(CONFIGURATION['imap']['server'], CONFIGURATION['imap']['port'])

    password = CONFIGURATION['imap']['credentials']['password']
    username = CONFIGURATION['imap']['credentials']['username']

    mail.login(username, password)
    mail.select('Inbox')

    # only check unseen emails
    try:
        from_address = CONFIGURATION['imap']['from_address']
        typ, data = mail.search(None, f'(UNSEEN FROM "{from_address}")')
    except Exception:
        typ, data = mail.search(None, f'(UNSEEN)')

    for num in data[0].split():
        LOGGER.debug("New mail detected, processing...")
        typ, data = mail.fetch(num, '(RFC822)')
        msg = message_from_bytes(data[0][1])

        for part in msg.walk():
            #find the attachment part - so skip all the other parts
            if part.get_content_maintype() == 'multipart': continue
            if part.get_content_maintype() == 'text': continue
            if part.get('Content-Disposition') == 'inline': continue
            if part.get('Content-Disposition') is None: continue
            # print only pdf
            if part.get_content_type() == 'application/pdf':
                LOGGER.info("Printing mail attachment")
                print_pdf(part.get_payload(decode=True),CONFIGURATION['printer']['name'])
            elif part.get_filename().split("?")[-2].endswith(".pdf"):
                LOGGER.info("Printing mail attachment")
                print_pdf(part.get_payload(decode=True),CONFIGURATION['printer']['name'])
