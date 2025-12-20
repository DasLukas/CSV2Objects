# CSV2Objects

CSV2Objects ist ein FreeCAD-Addon (Workbench), mit dem sich massenhaft
3D-Objekte mit Text aus CSV-Dateien erzeugen lassen.

## Features

-   Liest CSV-Dateien (konfigurierbares Encoding, Delimiter)
-   Verknüpft CSV-Spalten mit horizontalen Hilfslinien in Sketches
-   Erzeugt ShapeStrings + Extrusion auf Basis einer Font-Datei (System- oder Custom-Font)
-   Live-Preview der ersten CSV-Zeile im Dokument
-   Optionaler Boolean-Fuse mit einem Zielkörper pro CSV-Zeile
-   Export nach STL, 3MF oder STEP in einen Unterordner _[FCStd-Name]_
-   Dokument wird nach finalem Export in den Ursprungszustand zurückgesetzt

## Installation (manuell)

1. Repo/ZIP in den FreeCAD `Mod`-Ordner entpacken, so dass der Ordner  
   `CSV2Objects` direkt unterhalb von `Mod/` liegt.
2. FreeCAD neu starten.
3. In der Workbench-Liste `CSV2Objects` auswählen.

## Nutzung

1. Ein Dokument mit Sketch (Hilfslinien) und optionalem Zielkörper öffnen.
2. Workbench `CSV2Objects` aktivieren.
3. Toolbar-Button `CSV2Objects` klicken, um den Task-Dialog zu öffnen.
4. CSV-Datei, Encoding und Delimiter wählen.
5. Hilfslinien scannen und den gewünschten CSV-Spalten zuweisen.
6. Font, Extrusionshöhe und Exportformat wählen.
7. Mit `OK` den Export starten.
8. Mit `Cancel` den Dialog schließen (und Preview zurücksetzen).
