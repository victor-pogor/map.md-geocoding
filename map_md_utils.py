# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MapMd Utility Class.
                                 A QGIS plugin
 This plugin uses Map.md API.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2019-05-21
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Victor Pogor
        email                : victor.pogor@outlook.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import csv
import codecs
import sqlite3
import urllib.parse
import re
import requests
import shapely

from shapely.geometry import shape

# pylint: disable=import-error
from qgis.utils import iface
from qgis.core import (QgsDataSourceUri, Qgis,
                       QgsTask, QgsMessageLog)
# pylint: enable=import-error


class MapMdUtils(QgsTask):
    """ MapMdUtils Class.

    param input_filename: Input CSV absolute path.
    type input_filename: str

    param output_filename: Output SpatiaLite absolute path.
    type output_filename: str

    param notfound_filename: Output Not Found CSV absolute path.
    type notfound_filename: str

    param api_key: The Map.md API-key.
    type api_key: str

    param street1_index: Street 1 column index.
    type street1_index: int

    param street2_index: Street 2 column index.
    type street2_index: int

    param house_number_index: House number column index.
    type house_number_index: int

    param locality_index: Locality column index.
    type locality_index: int
    """

    def __init__(self, input_filename, output_filename="",
                 notfound_filename="", api_key="",
                 street1_index=-1, street2_index=-1,
                 house_number_index=-1, locality_index=-1):
        super().__init__("Geocodificarea adreselor", QgsTask.CanCancel)
        self.__api_key = api_key
        self.__street1_index = street1_index
        self.__street2_index = street2_index
        self.__house_number_index = house_number_index
        self.__locality_index = locality_index
        self.__input_filename = input_filename
        self.__output_filename = output_filename
        self.__notfound_filename = notfound_filename
        self.__table_name = "point_geometry"
        self.__header = [self.__quote_identifier(
            item) for item in next(self.read_csv())]
        self.__not_found_count = 0
        self.exception = None

    def __count_csv_lines(self):
        """ Count CSV lines. """
        try:
            with open(self.__input_filename, 'r', encoding='utf-8') as csvfile:
                return sum(1 for row in csvfile)
        except csv.Error:
            iface.messageBar().pushCritical(
                "Input CSV File",
                "Bad CSV file - verify that your delimiters are consistent")

    def __write_notfound_street_to_csv(self, row):
        """ Write not found street to CSV file.

        param line: Line to be written in CSV file.
        type line: str
        """
        with open(self.__notfound_filename, mode='a', newline='') as csvfile:
            csv_writter = csv.writer(
                csvfile, delimiter=',',
                quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writter.writerow(row)

        self.__not_found_count += 1
        QgsMessageLog.logMessage(
            "Nu a fost geocodificat rândul CSV: %s" % ','.join(row),
            level=Qgis.Warning)

    def __init_spatialite_db(self):
        """ Init SpatiaLite database."""
        with sqlite3.connect(self.__output_filename) as conn:
            conn.enable_load_extension(True)
            conn.load_extension("mod_spatialite")
            conn.execute("SELECT InitSpatialMetaData(1);")
            conn.execute("""CREATE TABLE IF NOT EXISTS %s (
                            PointId INTEGER NOT NULL
                            PRIMARY KEY AUTOINCREMENT);""" % self.__table_name)
            conn.execute("""CREATE UNIQUE INDEX IF NOT EXISTS
                            idx_%s_id ON
                            %s (PointId);""" % (self.__table_name,
                                                self.__table_name))

            cur = conn.cursor()
            cur.execute("PRAGMA table_info('%s');" % self.__table_name)
            db_columns = cur.fetchall()
            db_columns = (x[1] for x in db_columns)
            db_columns = [self.__quote_identifier(x) for x in db_columns]

            for column in self.__header:
                # Se adauga coloanele care nu au existat anterior
                if column not in db_columns:
                    conn.execute("""ALTER TABLE %s
                                    ADD COLUMN %s TEXT""" %
                                 (self.__table_name, column))

            # Se adauga coloana ce contine date geospatiale
            # cu geoproiectia WSG 84 (4326)
            if "Geometry" not in db_columns:
                conn.execute(
                    """SELECT AddGeometryColumn(
                        'point_geometry', 'Geometry',
                        4326, 'POINT', 'XY');""")

                # Se adauga index geospatial
                conn.execute(
                    "SELECT CreateSpatialIndex('point_geometry', 'Geometry');")

    def __add_row_to_db(self, row, geometry):
        """ Add CSV row to database.

        param csv_row: CSV row.
        type csv_row: list of str

        param geometry: Point geometry.
        type geometry: str
        """
        with sqlite3.connect(self.__output_filename) as conn:
            conn.enable_load_extension(True)
            conn.load_extension("mod_spatialite")
            cur = conn.cursor()

            # Insert it.
            sql = """INSERT INTO point_geometry
                    (%s, Geometry) VALUES
                    (%s, GeomFromText('%s', 4326));""" % \
                (
                    ','.join(self.__header),
                    ','.join([self.__quote_identifier(item)
                              for item in row]),
                    geometry
                )
            cur.execute(sql)

    def __add_spatialite_layer_to_qgis(self):
        """ Add SpatiaLite layer to the current QGIS project. """
        uri = QgsDataSourceUri()
        uri.setDatabase(self.__output_filename)
        schema = ''
        geom_column = 'Geometry'
        uri.setDataSource(schema, self.__table_name, geom_column)

        display_name = 'Addresses'
        vlayer = iface.addVectorLayer(uri.uri(), display_name, 'spatialite')
        if not vlayer:
            iface.messageBar().pushCritical(
                "Eroare încărcare strat",
                "A apărut o eroare la încărcarea stratului SpatiaLite")

    def __quote_identifier(self, s, errors="replace"):
        """ Quote identifier method.

        :param s: String.
        :type s: str

        :param errors: Error type. Should be:
            'strict': raise an exception in case of an encoding error
            'replace': replace malformed data with a suitable
            replacement marker, such as '?' or '\ufffd'
            'ignore': ignore malformed data and continue without further notice
            'xmlcharrefreplace': replace with the appropriate XML character
                reference (for encoding only)
            'backslashreplace': replace with backslashed escape sequences
                (for encoding only)
        :type errors: str

        return: Return parsed string.
        rtype: str
        """
        encodable = s.encode("utf-8", errors).decode("utf-8")
        nul_index = encodable.find("\x00")

        if nul_index >= 0:
            error = UnicodeEncodeError("NUL-terminated utf-8", encodable,
                                       nul_index, nul_index + 1,
                                       "NUL not allowed")
            error_handler = codecs.lookup_error(errors)
            replacement, _ = error_handler(error)
            encodable = encodable.replace("\x00", replacement)

        return "\"" + encodable.replace("\"", "\"\"") + "\""

    def __map_md_search_street(self, row, street):
        """ Map.md search street method.

        param row: Row list.
        type row: list of str

        param street: Street.
        type street: str

        :return: False or JSON
        :rtype: dict of str
        """
        locality = row[self.__locality_index]

        r = requests.get(
            "https://map.md/api/companies/webmap/search_street?" +
            "location=%s&q=%s" % (urllib.parse.quote(locality),
                                  urllib.parse.quote(street)),
            auth=(self.__api_key, ""))

        if not r or not r.json():
            self.__write_notfound_street_to_csv(row)
            return False
        return r.json()

    def __map_md_get_street(self, street_id, row):
        """ Map.md get street method.

        param street_id: The Map.md street id.
        type street_id: int

        param row: Row list.
        type row: list of str

        :return: False or JSON
        :rtype: dict of str
        """
        locality = row[self.__locality_index]
        r = requests.get(
            "https://map.md/api/companies/webmap/get_street?" +
            "id=%s&location=%s" % (urllib.parse.quote(street_id),
                                   urllib.parse.quote(locality)),
            auth=(self.__api_key, ""))

        if not r or not r.json():
            self.__write_notfound_street_to_csv(row)
            return False
        return r.json()

    def __map_md_search_street_with_house_number(self, row, street_id,
                                                 house_number):
        """ Map.md search street with house number method.

        param row: Row list.
        type row: list of str

        param house_number: House number.
        type house_number: str

        :return: False or JSON
        :rtype: dict of str
        """
        r = requests.get(
            "https://map.md/api/companies/webmap/get_street?" +
            "id=%s&number=%s" % (urllib.parse.quote(street_id),
                                 urllib.parse.quote(house_number)),
            auth=(self.__api_key, ""))

        if not r or not r.json():
            self.__write_notfound_street_to_csv(row)
            return False
        return r.json()

    def __geocode_street_and_house_number(self, row, street, house_number):
        """ Geocode street1 and house number.

        param row: Row list.
        type row: list of str

        param street: Street.
        type street: str

        param house_number: House number.
        type house_number: str

        :return: Return bool.
        :rtype: bool
        """
        r = self.__map_md_search_street(row, street)
        if not r:
            return False

        # Se obtine lista cu numerele caselor adresei solicitate
        buildings = r[0]['buildings']

        # Daca numarul casei nu se gaseste in lista,
        # nu se indeplineste cel de-al doilea request
        if house_number not in buildings:
            self.__write_notfound_street_to_csv(row)
            return False

        r = self.__map_md_search_street_with_house_number(
            row, r[0]['id'], house_number)
        if not r:
            return False

        geometry = "POINT(%s %s)" % (r['point']['lon'],
                                     r['point']['lat'])
        self.__add_row_to_db(row, geometry)

    def __geocode_street1_and_street2(self, row, street1, street2):
        """ Geocode street1 and street2.

        param row: Row list.
        type row: list of str

        param street: Street1.
        type street: str

        param street: Street2.
        type street: str

        :return: Return bool.
        :rtype: bool
        """
        # Se cauta strada1 pentru a obtine identificatorul ei
        r1 = self.__map_md_search_street(row, street1)

        # Se cauta strada2 pentru a obtine identificatorul ei
        r2 = self.__map_md_search_street(row, street2)

        # Verificare strada1 si strada2
        if not r1 or not r2:
            return False

        # Se obtine datele despre strada1
        r1 = self.__map_md_get_street(r1[0]['id'], row)
        r2 = self.__map_md_get_street(r2[0]['id'], row)
        if not r1 or not r2:
            return False

        r1_geo_json = r1['geo_json']
        r2_geo_json = r2['geo_json']

        s1 = shape(r1_geo_json)
        s2 = shape(r2_geo_json)

        if not s1.intersects(s2):
            self.__write_notfound_street_to_csv(row)
            return False

        geometry = s1.intersection(s2)

        # In cazul ca se identifica MultiPoint,
        # se ia primul Point in consideratie
        if isinstance(geometry,
                      shapely.geometry.multipoint.MultiPoint):
            geometry = geometry[0]

        self.__add_row_to_db(row, geometry.wkt)

    def read_csv(self):
        """ Read CSV file. """
        try:
            with open(self.__input_filename, 'r', encoding='utf-8') as csvfile:
                # Identify CSV dialect (delimiter)
                dialect = csv.Sniffer().sniff(csvfile.read(4096))
                csvfile.seek(0)
                reader = csv.reader(csvfile, dialect)

                for row in reader:
                    yield row
        except IOError:
            iface.messageBar().pushCritical(
                "Input CSV File",
                "Failure opening " + self.__input_filename)
        except UnicodeDecodeError:
            iface.messageBar().pushCritical(
                "Input CSV File",
                "Bad CSV file - Unicode decode error")
        except csv.Error:
            iface.messageBar().pushCritical(
                "Input CSV File",
                "Bad CSV file - verify that your delimiters are consistent")

    def run(self):
        """ Geocode addresses using Map.md API.

        return: Return bool type.
        type: bool
        """
        QgsMessageLog.logMessage("Început geocodificare.", level=Qgis.Info)

        # Se initializeaza baza de date SpatiaLite
        self.__init_spatialite_db()

        pattern = r"^((?:[a-z0-9ăîșțâ]+[\., ]+)+)(\d{1,3}(?:[\/ ]?\w{1,2})?)$"

        if self.__street1_index == -1 and self.__locality_index == -1:
            self.exception = Exception(
                "Indicele câmpurilor street1 și/sau locality sunt goale!")

        # Se omite primul rand, deoarece contine denumirile coloanelor
        iter_rows = iter(self.read_csv())
        next(iter_rows)

        for index, row in enumerate(iter_rows):
            self.setProgress(index*100/self.__count_csv_lines())
            # check isCanceled() to handle cancellation
            if self.isCanceled():
                return False

            if not row[self.__street1_index] and \
                    not row[self.__locality_index]:
                self.__write_notfound_street_to_csv(row)

            elif self.__street2_index > -1 and \
                    row[self.__street2_index]:

                QgsMessageLog.\
                    logMessage("Street1 + Street2 + Locality",
                               level=Qgis.Info)

                geocode_street1_and_street2 = \
                    self.__geocode_street1_and_street2(
                        row,
                        row[self.__street1_index],
                        row[self.__street2_index])

                if not geocode_street1_and_street2:
                    continue

            elif self.__house_number_index > -1 and \
                    row[self.__house_number_index]:

                QgsMessageLog.\
                    logMessage("Street1 + House number + Locality",
                               level=Qgis.Info)

                geocode_street_and_house_number = \
                    self.__geocode_street_and_house_number(
                        row,
                        row[self.__street1_index],
                        row[self.__house_number_index])
                if not geocode_street_and_house_number:
                    continue

            else:
                QgsMessageLog.logMessage("Street1 + Locality",
                                         level=Qgis.Info)
                match = re.search(pattern,
                                  row[self.__street1_index],
                                  re.IGNORECASE | re.UNICODE)
                if not match:
                    self.__write_notfound_street_to_csv(row)
                    continue

                street = match.group(1).replace(',', '').strip()
                house_number = match.group(2).strip()

                geocode_street_and_house_number = \
                    self.__geocode_street_and_house_number(
                        row, street, house_number)
                if not geocode_street_and_house_number:
                    continue

        return True

    def finished(self, result):
        """
        This function is automatically called when the task has
        completed (successfully or not).
        You implement finished() to do whatever follow-up stuff
        should happen after the task is complete.
        finished is always called from the main thread, so it's safe
        to do GUI operations and raise Python exceptions here.
        result is the return value from self.run.
        """
        if result:
            # Se adauga stratul in QGIS
            self.__add_spatialite_layer_to_qgis()

            csv_row_count = self.__count_csv_lines()

            QgsMessageLog.logMessage(
                "Sfârșit geocodificare." +
                "Au fost geocodificate %i din %i adrese." %
                (csv_row_count-self.__not_found_count, csv_row_count),
                level=Qgis.Success)
        elif self.exception is None:
            # Se adauga stratul in QGIS
            self.__add_spatialite_layer_to_qgis()

            QgsMessageLog.logMessage(
                "Geocodificarea a fost anulată. " +
                "Se afișează rezultatele obținute până la moment.",
                level=Qgis.Warning)
        else:
            QgsMessageLog.logMessage(
                "Procesul de geocodificare a returnat o excepție:\n%s" %
                str(self.exception), level=Qgis.Critical)
            raise self.exception
