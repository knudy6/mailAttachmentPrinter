# Automatically Print Mail Attachments

## Requirements

- Installed [CUPS](https://www.cups.org/)

## Functions

- Print E-Mail Attachments received from an IMAP mail server
- Set status of printed E-Mails to 'read'

## Configuration

You can either configure the script via config file or environment variables.

**Keep in mind:**
- If a config file is provided all environment variables are ignored.
- The configuration file must include all configuration entries.

#### Config file

Location: /\<workdir\>/config/config.json</br>
Example: [config/config.json.example](config/config.json.example)

#### Environment variables
|      Required      |                Env variable | Possible values                                 | Default value | Description                                                                                                         |
| :----------------: | --------------------------: | :---------------------------------------------- | :-----------: | :------------------------------------------------------------------------------------------------------------------ |
| :white_check_mark: | `IMAP_CREDENTIALS_PASSWORD` | `s3cr3tp4ssw0rd`                                |      :x:      | Passwort to authenticate to imap server                                                                             |
| :white_check_mark: | `IMAP_CREDENTIALS_USERNAME` | `some@email.domain`                             |      :x:      | Username to authenticate to imap server                                                                             |
|                    |            `IMAP_FORCE_SSL` | `TRUE\|FALSE`                                   |    `TRUE`     | Force SSL connection to imap server                                                                                 |
|                    |         `IMAP_FROM_ADDRESS` | `from@email.domain`                             |      :x:      | From mail address to print only attachments from this address (prints attachments from all mail addresses if empty) |
|                    |                 `IMAP_PORT` | `0-∞`                                           |     `993`     | Connection port of imap server                                                                                      |
| :white_check_mark: |               `IMAP_SERVER` | `server.mail.domain`                            |      :x:      | Address of imap server                                                                                              |
|                    |                 `LOG_LEVEL` | `CRITICAL\|ERROR\|WARNING\|INFO\|DEBUG\|NOTSET` |    `INFO`     | Sets the logging level                                                                                              |
| :white_check_mark: |              `PRINTER_NAME` | `Printer_XYZ`                                   |      :x:      | Name of Printer (provided by CUPS)                                                                                  |
| :white_check_mark: |            `PRINTER_SERVER` | `printer.server.domain`                         |      :x:      | Address of CUPS Printer Server                                                                                      |
|                    |             `SCAN_INTERVAL` | `0-∞`                                           |     `10`      | Mail scan interval in seconds                                                                                       |

## Installation

### Docker

Requirements:

- Installed [Docker](https://docs.docker.com/get-docker/)

Build the Docker container:
1. Clone this repository
2. Go into the directory</br>
   `cd mailAttachmentPrinter`
3. Build Docker container</br>
   `docker build -t mailattachmentprinter:v1.0 .`

Run the Docker container manual:
1. Copy the preferred configuration methode</br>
   config file: `cp config/config.json.example config/config.json`</br>
   environment variables: `cp env.example env`
2. Start the docker container:</br>
   config file: `docker run -d --restart on-failure -v ./config:/app/config mailattachmentprinter:v1.0`</br>
   environment variables: `docker run -d --restart on-failure --env-file ./env mailattachmentprinter:v1.0`

Run the Docker container with [Docker Compose](https://docs.docker.com/compose/install/):

1. Copy the preferred configuration methode</br>
   config file: `cp config/config.json.example config/config.json`</br>
   environment variables: `cp env.example env`
2. Start the docker-compose stack:
   `docker-compose up -d`

### As script

Requirements:
- Installed [Python3](https://www.python.org/downloads/) (Tested with Python3.12)
- Installed Python requirements `pip3 install -r requirements`

1. Clone this repository
2. Go into the directory</br>
   `cd mailAttachmentPrinter`
3. Copy the preferred configuration methode</br>
   config file: `cp config/config.json.example config/config.json`</br>
   environment variables: `cp env.example env`
4. Start the script</br>
   `python3 entrypoint.py`
