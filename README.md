# Map.md Geocoding QGIS plugin

Această extensie folosește serviciul Map.md API pentru geocodificarea adreselor din fișierul CSV UTF-8.
![Interfața extensiei Map.md Geocoding QGIS plugin](https://i.ibb.co/LCbC7Xh/Annotation-2019-06-12-152915.png)

## Sursa de inspirație

Ideea de a crea această extensie mi-a venit după publicarea pe blogul site-ului map.md a [informației](https://map.md/ru/blog/map-md-lanseaza-setul-de-servicii-api) cu privire la lansarea serviciului API gratuit și nelimitat.
Sursa de inspirație pentru elaborarea acestei extensii a servit o altă extensie existentă cu denumirea [MMQGIS](https://plugins.qgis.org/plugins/mmqgis/).
Aceasta geocodifică adresele folosind serviciile [Google Geocoding API](https://developers.google.com/maps/documentation/geocoding/start) și [OSM Nominatim](https://nominatim.openstreetmap.org/), dar are următoarele neajunsuri:

* Nu are funcționalitatea de geocodificare a intersecțiilor
* Blochează interfața utilizatorului și nu arată progresul geocodificării.
* Rezultatul geocodificării se stochează într-un fișier cu extensia [SHP](https://en.wikipedia.org/wiki/Shapefile). Acesta, la rândul său, are următoarele limite și dezavantaje:
  * Lungimea denumirii coloanelor nu poate depăși 10 caractere;
  * Suport slab a codificării Unicode;
  * Pe lângă fișierul cu extensia SHP, în aceeași mapă se mai stocau și alte fișiere cu diverse extensii (*.cpg, *.dbf, *.prj, *.qpj, *.shx).

## Tipuri de geocodificări

Extensia Map.md Geocoding funcționează cu versiunea QGIS 3 și are următoarele tipuri de geocodificări:

* Geocodificarea străzii, casei și localității;
* Geocodificarea străzii și localității, când casa se conține in câmpul cu strada;
* Geocodificarea intersecțiilor (strada1, strada2, localitate);
* Geocodificarea combinată (se alege una din cele enunțate mai sus, în dependență de ce câmpuri sunt indeplinite).

## Alte funcționalități

* Nu blochează intefața utilizatorului, indicând în managerul de sarcini (Task Manager) al aplicației QGIS progresul de geocodificare;
* Salvează rezultatele geocodificării în bază de date de tip SpatiaLite.

## Cum să obțin o cheie API

Pentru a utiliza serviciile API Map.md, este necesar să obțineți un cod unic de identificare. Pentru aceasta, trebuie să vă conectați la sistemul Simpals-ID, utilizând login-ul sau parola contului dvs. pentru oricare dintre proiectele companiei (de exemplu, 999.md sau point.md).

Apoi, accesați link-ul [map.md/ro/api](map.md/ro/api) sau deschideți secțiunea "API" de pe site-ul [map.md](https://map.md), care se află în rubrica "Info".

Apoi, după ce ați făcut click pe butonul "Obțineți codul", completați formularul special. În câmpul "Website", introduceți adresa URL a site-ului dvs. (mai bine să specificați doar numele de domeniu). În câmpurile iOS și Android, indicați numele aplicației. În continuare, salvați codul rezultat. Rețineți, codul stocat pentru un anumit nume de domeniu este valabil pentru toate adresele URL din interiorul acestuia și pentru numele de subdomenii speciale.

**Important!** Codul de identificare este generat numai de către proprietarul proiectului.

## Procedura de development și debugging al extensiei

Pentru un development și debugging cu succes este nevoie de urmat instrucțiunea următoare ce se referă la sistemul de operare Windows.

1. Descărcați [OSGeo4W](https://qgis.org/en/site/forusers/download.html) de pe pagina oficială a aplicației QGIS și instalați-l pe calculatorul Dvs., selectând opțiunea *Desktop Express Install* în installer.

2. Descărcați sau clonați repository-ul în mapa `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\map_md_geocoding`.

3. Instalați și rulați [Visual Studio Code](https://code.visualstudio.com/) prin intermediul fișierului `start_vscode.cmd`. Aceasta va seta toate variabilele de mediu necesare pentru rularea codului și pentru IntelliSense.

4. Rulați aplicația QGIS și instalați extensiile *Plugin Reloader* și *debugvs*. Prima extensie va permite reinstalarea extensiei date fără repornirea aplicației QGIS. Extensia *debugvs* va permite debugging-ul direct in Visual Studio Code.

## Mulțumiri

Aduc sincere mulțumiri companiei [Simpals](https://simpals.com), pentru furnizarea serviciului gratuit și nelimitat Map.md API.
