# CSV2Objects

CSV2Objects is a FreeCAD workbench that generates **large batches** of 3D objects with **CSV-driven text** placed on sketch guide lines.

## Features

- Reads CSV files (configurable encoding and delimiter)
- Maps CSV columns to sketch reference lines
- Creates `ShapeString` objects on the sketch plane and extrudes them
- Live preview using the first CSV row (while the dialog is open)
- Optional boolean fuse with a target solid per generated row
- Export formats: **STL**, **3MF**, or **STEP**
- Exports into a subfolder named after the current `.FCStd` file
- Restores the original document state after the final export

## Manual installation

1. Copy or unzip this repository into your FreeCAD `Mod/` folder so the structure looks like:

    ```text
    Mod/
    └─ CSV2Objects/
       ├─ Init.py
       ├─ InitGui.py
       └─ ...
    ```

2. Restart FreeCAD.
3. Select the **CSV2Objects** workbench.

## Usage

1. Open a document containing a sketch with reference lines (and optionally a target solid).
2. Switch to the **CSV2Objects** workbench.
3. Click the **CSV2Objects** toolbar button to open the task dialog.
4. Select a CSV file, encoding, and delimiter.
5. Scan/select reference lines and map them to CSV columns.
6. Choose font, extrusion height, and export format.
7. Press **OK** to run the export (dialog stays open).
8. Press **Cancel** to close the dialog (and clear preview objects).

## Notes

- The dock overlay “X” in the Tasks panel toggles the left overlay panel and does _not_ close a task dialog. Use **Cancel** to close the CSV2Objects dialog.

## Links

- GitHub: https://github.com/DasLukas/CSV2Objects

## License

MIT License. See `LICENSE`.
