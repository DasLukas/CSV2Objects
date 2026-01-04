# CSV2Objects

CSV2Objects is a FreeCAD **macro** that generates large batches of 3D objects with CSV-driven text placed on sketch guide lines.

## Features

- Reads CSV files (configurable encoding and delimiter)
- Maps CSV columns to sketch reference lines
- Creates `ShapeString` objects on the sketch plane and extrudes them
- Live preview using the first CSV row (while the dialog is open)
- Optional boolean fuse with a target solid per generated row
- Export formats: **STL**, **3MF**, or **STEP**
- Exports into a subfolder named after the current `.FCStd` file
- Restores the original document state after the final export

## Manual installation (macro)

1. Copy `CSV2Objects.FCMacro` into your FreeCAD macro directory (e.g. `~/Library/Preferences/FreeCAD/Macro` on macOS).
2. Restart FreeCAD (or reload macros).
3. In FreeCAD, open **Macro > Macros…**, select **CSV2Objects.FCMacro**, and click **Execute** to launch the dialog.

## Usage

1. Open a document containing a sketch with reference lines (and optionally a target solid).
2. Run the **CSV2Objects.FCMacro** (Macro > Macros…).
3. In the dialog: select a CSV file, encoding, and delimiter.
4. Scan/select reference lines and map them to CSV columns.
5. Choose font, extrusion height, and export format.
6. Press **OK** to run the export (dialog stays open).
7. Press **Cancel** to close the dialog (and clear preview objects).

## Notes

- The dock overlay “X” in the Tasks panel toggles the left overlay panel and does _not_ close a task dialog. Use **Cancel** to close the CSV2Objects dialog.

## Links

- GitHub: https://github.com/DasLukas/CSV2Objects

## License

MIT License. See `LICENSE`.
