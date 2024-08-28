"""mailAttachmentPrinter tides"""
from csv import reader
from datetime import datetime,timedelta
from io import BytesIO
from os import listdir
from os.path import join
from pytz import utc
from sys import exit
from markdown2 import markdown
from weasyprint import HTML

from .config import LOGGER,TIDES_DELIMITER,TIDES_DIRECTORY,TIDES_ENCODING,TIDES_TIMEZONE
from .printer import print_pdf

ICON_HIGH_TIDE = '<svg height="1em" width="1em" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M20 7H22V9H20C18.62 9 17.26 8.65 16 8C13.5 9.3 10.5 9.3 8 8C6.74 8.65 5.37 9 4 9H2V7H4C5.39 7 6.78 6.53 8 5.67C10.44 7.38 13.56 7.38 16 5.67C17.22 6.53 18.61 7 20 7M12 11L16 15H13V22H11V15H8L12 11Z" /></svg>'
ICON_LOW_TIDE = '<svg height="1em" width="1em" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M20 7H22V9H20C18.62 9 17.26 8.65 16 8C13.5 9.3 10.5 9.3 8 8C6.74 8.65 5.37 9 4 9H2V7H4C5.39 7 6.78 6.53 8 5.67C10.44 7.38 13.56 7.38 16 5.67C17.22 6.53 18.61 7 20 7M12 22L8 18H11V11H13V18H16L12 22Z" /></svg>'
ICON_NEW_MOON = '<svg height="1em" width="1em" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 20A8 8 0 1 1 20 12A8 8 0 0 1 12 20M12 2A10 10 0 1 0 22 12A10 10 0 0 0 12 2Z" /></svg>'
ICON_FIRST_QUARTER_MOON = '<svg height="1em" width="1em" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2A10 10 0 0 0 12 22Z" /></svg>'
ICON_FULL_MOON = '<svg height="1em" width="1em" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2A10 10 0 1 1 2 12A10 10 0 0 1 12 2Z" /></svg>'
ICON_LAST_QUARTER_MOON = '<svg height="1em" width="1em" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2V22A10 10 0 0 0 12 2Z" /></svg>'
QUELLE_URL = "https://tableau.bsh.de/views/Gezeitenvorausberechnung_V02/Download-Bereich"

def check_requirements(configuration):
    """check if all required files are present"""
    LOGGER.debug("Check Requirements for tides extension")
    # set 'required' variables
    ## from configuration
    required_stations = configuration["tide"]["stations"]

    ## years
    _current_year = datetime.now(utc).astimezone(TIDES_TIMEZONE).strftime("%Y")
    _next_year = (datetime.now(utc).astimezone(TIDES_TIMEZONE) + timedelta(365)).strftime("%Y")
    required_years = [_current_year,_next_year] if int(datetime.now(utc).astimezone(TIDES_TIMEZONE).strftime("%m")) >= 11 else [_current_year]

    # build checklist
    checklist = {}
    for station in required_stations:
        checklist.update({station:{}})
        for year in required_years:
            checklist[station].update({year:False})

    LOGGER.debug("Check what files should be present...")
    #  parse files and fill checklist
    files = _get_files()
    for file in files:
        meta_data = _get_meta_data(_get_data_from_file(file))
        try:
            checklist[meta_data["station"]][meta_data["year"]] = True
        except KeyError:
            continue

    LOGGER.debug("Check if files are present...")
    # prepare error message
    missing_stations_years = []
    for station,data in checklist.items():
        _missing_years = []
        for year,satisfied in data.items():
            if not satisfied:
                _missing_years.append(year)
        if _missing_years != []:
            missing_stations_years.append(f"Station: '{station}' Years: {', '.join(_missing_years)}")

    # Error output
    if missing_stations_years != []:
        LOGGER.critical("From the following years the following years are missing:")
        for station in missing_stations_years:
            LOGGER.critical(station)
        exit(-1)
    LOGGER.debug("All required files are present.")

def _get_files() -> list:
    """return file locations as a list"""
    LOGGER.debug("Get all tide files")
    files = listdir(TIDES_DIRECTORY)
    full_files = [join(TIDES_DIRECTORY,file) for file in files]
    return full_files

def _get_data_from_file(file) -> list:
    """get data from file and return it as a list"""
    data = []

    LOGGER.debug("Read data from file: %s" % file)
    file_in = open(file,"r",encoding=TIDES_ENCODING)
    for row in reader(file_in,delimiter=TIDES_DELIMITER):
        data.append(row)
    return data

def _get_tide_data(data) -> list:
    """return a list with all tide events"""
    tide_data = []
    LOGGER.debug("Extract Tide specific data from data")
    for row in data:
        if row[0] == "VB2":
            tide_data.append(row)
    return tide_data

def _get_meta_data(data) -> dict:
    """return a dict with meta data"""
    LOGGER.debug("Read meta data from file")
    for row in data:
        if row[0] == "A03":
            station = row[2].replace(" ","")
        if row[0] == "A04":
            name = row[2].replace(" ","")
        if row[0] == "A06":
            year = row[2].replace(" ","")

    data = {"station": station,"name": name, "year": year}
    return data

def _filter_data_for_relevant_data(tide_data) -> list:
    """filter data fot the last 2 and next 2 events based on current time"""
    LOGGER.debug("Filter for the last 2 and next 2 tide events")
    current_time = datetime.now(utc).astimezone(TIDES_TIMEZONE)
    previous_two = []
    next_two = []

    for i, row in enumerate(tide_data):
        row_date = datetime.strptime(row[5].replace(" ","") + ";"+ row[6].replace(" ","") + ";+0100", "%d.%m.%Y;%H:%M;%z")

        if row_date > current_time:
            previous_two = tide_data[max(0, i-2):i]
            next_two = tide_data[i:min(i+2, len(tide_data))]
            break

    relevant_tide_events = previous_two + next_two
    return relevant_tide_events

def _generate_tide_type_text(tide_type:str):
    """return corresponding icon based on tide type"""
    if tide_type == "H":
        text = "Hochwasser"
    elif tide_type == "N":
        text = "Niedrigwasser"
    else:
        text = ""
    return text

def _generate_tide_type_icon(tide_type:str):
    """return corresponding icon based on tide type"""
    if tide_type == "H":
        icon = ICON_HIGH_TIDE
    elif tide_type == "N":
        icon = ICON_LOW_TIDE
    else:
        icon = ""
    return icon

def _generate_moon_icon(moon_phase:str):
    """return corresponding icon based on moon phase"""
    if moon_phase == "0":
        icon = ICON_NEW_MOON
    elif moon_phase == "1":
        icon = ICON_FIRST_QUARTER_MOON
    elif moon_phase == "2":
        icon = ICON_FULL_MOON
    elif moon_phase == "3":
        icon = ICON_LAST_QUARTER_MOON
    else:
        icon = ""
    return icon

def _combine_data(configuration) -> dict:
    """combine all data into one dict"""
    all_data = {}
    LOGGER.debug("Combine all data from all stations")
    files = _get_files()
    for file in files:
        data = _get_data_from_file(file)
        meta_data = _get_meta_data(data)
        tide_data = _get_tide_data(data)
        if meta_data["station"] not in configuration["tide"]["stations"]:
            continue
        if meta_data["station"] in all_data.keys():
            all_data[meta_data["station"]]['data'].append(tide_data)
        else:
            new_data = {meta_data["station"]:{"name": meta_data["name"],"data": tide_data}}
            all_data.update(new_data)

    LOGGER.debug(all_data.keys())

    LOGGER.debug("Data from all stations acquired")
    return all_data

def _create_pdf(markdown_text: str) -> BytesIO:
    """convert markdown text to pdf"""
    pdf_out_bytes = BytesIO()
    LOGGER.debug("Convert markdown to pdf file")
    # markdown to html
    html_content = markdown(markdown_text)
    # html to pdf
    HTML(string=html_content).write_pdf(pdf_out_bytes)

    return pdf_out_bytes

def create_tide_overview(configuration):
    """parse tide data and print pdf"""
    _current_time = datetime.now().astimezone()
    all_data = _combine_data(configuration)

    LOGGER.debug("Generating markdown data from tide data")
    # generate header
    output_text = f"# Gezeiten Übersicht {_current_time.strftime('%d.%m.%Y')}\n\n" + \
        "---\n" + \
        "<style>body {font-size:0.75em;} table, th, td {border: 0px solid black;} :not(td:last-of-type) {padding-right: 1em;}</style>\n" + \
        "## Standorte:\n" + \
        "\n"

    # create data for each station
    for data in all_data:
        filtered_data = _filter_data_for_relevant_data(all_data[data]["data"])

        output_text += f"### {all_data[data]["name"]}"
        output_text += "\n"
        output_text += "<table>\n"
        output_text += "<tr>\n"
        output_text += f"<td>{_generate_tide_type_icon(filtered_data[0][3])}Letztes {_generate_tide_type_text(filtered_data[0][3])}</td>\n"
        output_text += f"<td>{datetime.strptime(filtered_data[0][6].replace(" ","") + "+0100","%H:%M%z").astimezone(_current_time.tzinfo).strftime("%H:%M")} Uhr</td>"
        output_text += f"<td>{filtered_data[0][7].replace(" ","").replace(".",",")}m</td>\n"
        output_text += f"<td>{_generate_moon_icon(filtered_data[0][2])}</td>\n"
        output_text += "</tr>\n"
        output_text += "<tr>\n"
        output_text += f"<td>{_generate_tide_type_icon(filtered_data[1][3])}Letztes {_generate_tide_type_text(filtered_data[1][3])}</td>\n"
        output_text += f"<td>{datetime.strptime(filtered_data[1][6].replace(" ","") + "+0100","%H:%M%z").astimezone(_current_time.tzinfo).strftime("%H:%M")} Uhr</td>"
        output_text += f"<td>{filtered_data[1][7].replace(" ","").replace(".",",")}m</td>\n"
        output_text += f"<td>{_generate_moon_icon(filtered_data[1][2])}</td>\n"
        output_text += "</tr>\n"
        output_text += "<tr>\n"
        output_text += f"<td>{_generate_tide_type_icon(filtered_data[2][3])}Nächstes {_generate_tide_type_text(filtered_data[2][3])}</td>\n"
        output_text += f"<td>{datetime.strptime(filtered_data[2][6].replace(" ","") + "+0100","%H:%M%z").astimezone(_current_time.tzinfo).strftime("%H:%M")} Uhr</td>"
        output_text += f"<td>{filtered_data[2][7].replace(" ","").replace(".",",")}m</td>\n"
        output_text += f"<td>{_generate_moon_icon(filtered_data[2][2])}</td>\n"
        output_text += "</tr>\n"
        output_text += "<tr>\n"
        output_text += f"<td>{_generate_tide_type_icon(filtered_data[3][3])}Nächstes {_generate_tide_type_text(filtered_data[3][3])}</td>\n"
        output_text += f"<td>{datetime.strptime(filtered_data[3][6].replace(" ","") + "+0100","%H:%M%z").astimezone(_current_time.tzinfo).strftime("%H:%M")} Uhr</td>"
        output_text += f"<td>{filtered_data[3][7].replace(" ","").replace(".",",")}m</td>"
        output_text += f"<td>{_generate_moon_icon(filtered_data[3][2])}</td>\n"
        output_text += "</tr>\n"
        output_text += "</table>\n"
        output_text += "\n"
        output_text += "---\n"

    # generate footer
    output_text += '\n<span style="font-size:0.65em;">Legende:\n'
    output_text += 'Hochwasser: ' + ICON_HIGH_TIDE + '\n'
    output_text += 'Niedrigwasser: ' + ICON_LOW_TIDE + '\n'
    output_text += 'Neumond: ' + ICON_NEW_MOON + '\n'
    output_text += 'Erster Halbmond: ' + ICON_FIRST_QUARTER_MOON + '\n'
    output_text += 'Vollmond: ' + ICON_FULL_MOON + '\n'
    output_text += 'Letzter Halbmond: ' + ICON_LAST_QUARTER_MOON + '</span>\n\n'
    output_text += f"\n<span style=\"font-size:0.65em;\">Stand: {_current_time.strftime('%d.%m.%Y, %H:%M Uhr')}</br>Quelle: " + QUELLE_URL + "</span>\n\n"

    pdf_bytes = _create_pdf(output_text)
    print_pdf(pdf_bytes.getvalue(),configuration['printer']['name'])
