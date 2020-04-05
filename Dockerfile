FROM qgis/qgis

WORKDIR /usr/src/map-md

COPY requirements.txt .

RUN pip3 install -r requirements.txt

RUN apt-get install zip

COPY . .
