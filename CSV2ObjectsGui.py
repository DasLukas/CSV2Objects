import FreeCAD as App
import FreeCADGui as Gui
import Part
import Draft
import Mesh
import ImportGui
import csv
import os
import sys
import glob

try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:
    from PySide import QtCore, QtGui, QtGui as QtWidgets


MAX_PATH_LEN = 240  # konservative Obergrenze für Pfadlängen


class TextFromCSVTaskPanel:
    """
    TaskPanel:
    - Text aus CSV auf Hilfslinien
    - ShapeString + Extrusion
    - Livepreview (erste CSV-Zeile)
    - optionaler Boolean-Fuse mit Zielkörper (pro CSV-Zeile eigene Kopie)
    - STL-Export in Unterordner neben der FCStd-Datei
    - Dokumentzustand nach finalem Export wieder herstellen
    """

    def __init__(self):
        self.doc = App.ActiveDocument
        if self.doc is None:
            raise RuntimeError("Kein aktives Dokument geöffnet.")

        # Preview-Objekte (ShapeStrings + Extrudes) der Livepreview
        self.preview_objects = []

        # ---------- Haupt-Widget ----------
        self.form = QtWidgets.QWidget()
        self.form.setWindowTitle("Text aus CSV auf Hilfslinien")

        main_layout = QtWidgets.QVBoxLayout(self.form)

        # -------------------------------------------------
        # CSV-Einstellungen
        # -------------------------------------------------
        csv_group = QtWidgets.QGroupBox("CSV-Einstellungen")
        csv_layout = QtWidgets.QGridLayout(csv_group)

        self.csv_path_edit = QtWidgets.QLineEdit()
        self.csv_browse_btn = QtWidgets.QPushButton("CSV wählen…")

        csv_layout.addWidget(QtWidgets.QLabel("CSV-Datei:"), 0, 0)
        csv_layout.addWidget(self.csv_path_edit, 0, 1)
        csv_layout.addWidget(self.csv_browse_btn, 0, 2)

        self.encoding_combo = QtWidgets.QComboBox()
        self.encoding_combo.addItems(["utf-8", "latin-1", "cp1252"])
        self.encoding_combo.setCurrentText("utf-8")

        csv_layout.addWidget(QtWidgets.QLabel("Encoding:"), 1, 0)
        csv_layout.addWidget(self.encoding_combo, 1, 1)

        self.delimiter_edit = QtWidgets.QLineEdit(";")
        self.delimiter_edit.setFixedWidth(40)
        csv_layout.addWidget(QtWidgets.QLabel("Delimiter:"), 2, 0)
        csv_layout.addWidget(self.delimiter_edit, 2, 1)

        self.load_csv_btn = QtWidgets.QPushButton("CSV einlesen")
        csv_layout.addWidget(self.load_csv_btn, 3, 0, 1, 3)

        main_layout.addWidget(csv_group)

        # -------------------------------------------------
        # Sketch / Hilfslinien
        # -------------------------------------------------
        sketch_group = QtWidgets.QGroupBox("Sketch & Hilfslinien")
        sketch_layout = QtWidgets.QVBoxLayout(sketch_group)

        hl1 = QtWidgets.QHBoxLayout()
        self.sketch_combo = QtWidgets.QComboBox()
        hl1.addWidget(QtWidgets.QLabel("Sketch:"))
        hl1.addWidget(self.sketch_combo)
        self.scan_lines_btn = QtWidgets.QPushButton("Hilfslinien scannen")
        hl1.addWidget(self.scan_lines_btn)
        sketch_layout.addLayout(hl1)

        self.lines_table = QtWidgets.QTableWidget()
        self.lines_table.setColumnCount(4)
        self.lines_table.setHorizontalHeaderLabels(
            ["Aktiv", "Geo-Index", "Y", "CSV-Spalte"]
        )
        self.lines_table.horizontalHeader().setStretchLastSection(True)
        self.lines_table.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)
        sketch_layout.addWidget(self.lines_table)

        main_layout.addWidget(sketch_group)

        # -------------------------------------------------
        # Text / Extrusion / Boolean / Livepreview
        # -------------------------------------------------
        geo_group = QtWidgets.QGroupBox("Text, Extrusion & Boolean")
        geo_layout = QtWidgets.QGridLayout(geo_group)

        # System-Fonts
        self.system_fonts = self._find_system_fonts()
        self.system_font_combo = QtWidgets.QComboBox()
        self.system_font_combo.addItem("– System-Font wählen –", "")
        for name, path in sorted(self.system_fonts.items()):
            self.system_font_combo.addItem(name, path)

        geo_layout.addWidget(QtWidgets.QLabel("System-Font:"), 0, 0)
        geo_layout.addWidget(self.system_font_combo, 0, 1, 1, 2)

        # Eigene Font-Datei
        self.font_path_edit = QtWidgets.QLineEdit()
        self.font_browse_btn = QtWidgets.QPushButton("Font-Datei wählen…")

        geo_layout.addWidget(QtWidgets.QLabel("TTF/OTF-Datei:"), 1, 0)
        geo_layout.addWidget(self.font_path_edit, 1, 1)
        geo_layout.addWidget(self.font_browse_btn, 1, 2)

        # FONT_SCALE
        self.font_scale_spin = QtWidgets.QDoubleSpinBox()
        self.font_scale_spin.setRange(0.05, 5.0)
        self.font_scale_spin.setSingleStep(0.05)
        self.font_scale_spin.setValue(0.7)

        geo_layout.addWidget(QtWidgets.QLabel("FONT_SCALE (rel. Höhe):"), 2, 0)
        geo_layout.addWidget(self.font_scale_spin, 2, 1)

        # Extrusionshöhe
        self.extrude_height_spin = QtWidgets.QDoubleSpinBox()
        self.extrude_height_spin.setRange(0.01, 50.0)
        self.extrude_height_spin.setSingleStep(0.1)
        self.extrude_height_spin.setValue(1.0)

        geo_layout.addWidget(QtWidgets.QLabel("Extrusionshöhe [mm]:"), 3, 0)
        geo_layout.addWidget(self.extrude_height_spin, 3, 1)

        # Boolean-Modus (nur final)
        self.boolean_mode_combo = QtWidgets.QComboBox()
        self.boolean_mode_combo.addItems([
            "Nur Textkörper erzeugen",
            "Mit Zielkörper verschmelzen (Fuse)"
        ])

        geo_layout.addWidget(QtWidgets.QLabel("Modus (nur final):"), 4, 0)
        geo_layout.addWidget(self.boolean_mode_combo, 4, 1)

        self.target_body_combo = QtWidgets.QComboBox()
        geo_layout.addWidget(QtWidgets.QLabel("Zielkörper (für Fuse):"), 5, 0)
        geo_layout.addWidget(self.target_body_combo, 5, 1, 1, 2)

        # Livepreview-Checkbox
        self.preview_check = QtWidgets.QCheckBox(
            "Livepreview der ersten CSV-Zeile (während der Dialog offen ist)"
        )
        self.preview_check.setChecked(True)
        geo_layout.addWidget(self.preview_check, 6, 0, 1, 3)

        # Exportformat
        self.export_format_combo = QtWidgets.QComboBox()
        self.export_format_combo.addItem("STL", "stl")
        self.export_format_combo.addItem("3MF", "3mf")
        self.export_format_combo.addItem("STEP", "step")

        geo_layout.addWidget(QtWidgets.QLabel("Exportformat:"), 7, 0)
        geo_layout.addWidget(self.export_format_combo, 7, 1)

        main_layout.addWidget(geo_group)

        # interne CSV-Daten
        self.csv_headers = []
        self.csv_rows = []

        # UI initial füllen
        self.populate_sketches()
        self.populate_bodies()

        # Signale verbinden
        self.csv_browse_btn.clicked.connect(self.on_browse_csv)
        self.load_csv_btn.clicked.connect(self.on_load_csv)
        self.scan_lines_btn.clicked.connect(self.on_scan_lines)
        self.font_browse_btn.clicked.connect(self.on_browse_font)
        self.system_font_combo.currentIndexChanged.connect(self.on_system_font_changed)
        self.sketch_combo.currentIndexChanged.connect(self.maybe_trigger_preview)
        self.font_scale_spin.valueChanged.connect(self.maybe_trigger_preview)
        self.extrude_height_spin.valueChanged.connect(self.maybe_trigger_preview)
        self.preview_check.stateChanged.connect(self.maybe_trigger_preview)

    # ---------- TaskPanel-API ----------

    def getStandardButtons(self):
        return int(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

    def accept(self):
        """OK-Button: Export ausführen, TaskPanel aber geöffnet lassen."""
        try:
            self.run_generation(preview=False)
        except Exception as e:
            App.Console.PrintError("Fehler: %s\n" % e)
            QtWidgets.QMessageBox.critical(self.form, "Fehler", str(e))
            # keine Rückgabe, TaskPanel bleibt offen

    def reject(self):
        """Cancel-Button / X: Preview zurücksetzen und TaskPanel schließen."""
        if self.preview_objects:
            for obj in list(self.preview_objects):
                if obj in self.doc.Objects:
                    try:
                        self.doc.removeObject(obj.Name)
                    except Exception:
                        pass
            self.preview_objects = []
            self.doc.recompute()

        # TaskPanel über FreeCAD sauber schließen
        try:
            Gui.Control.closeDialog()
        except Exception:
            pass

    # ---------- System-Fonts ----------

    def _find_system_fonts(self):
        font_dirs = []

        if sys.platform.startswith("win"):
            win_dir = os.environ.get("WINDIR", r"C:\Windows")
            font_dirs.append(os.path.join(win_dir, "Fonts"))
        elif sys.platform == "darwin":
            font_dirs.extend([
                "/System/Library/Fonts",
                "/Library/Fonts",
                os.path.expanduser("~/Library/Fonts"),
            ])
        else:
            font_dirs.extend([
                "/usr/share/fonts",
                "/usr/local/share/fonts",
                os.path.expanduser("~/.fonts"),
                os.path.expanduser("~/.local/share/fonts"),
            ])

        fonts = {}
        for d in font_dirs:
            if not os.path.isdir(d):
                continue
            for ext in ("*.ttf", "*.TTF", "*.otf", "*.OTF"):
                pattern = os.path.join(d, ext)
                for path in glob.glob(pattern):
                    name = os.path.basename(path)
                    fonts[name] = path

        return fonts

    def on_system_font_changed(self, index):
        path = self.system_font_combo.itemData(index)
        if path:
            self.font_path_edit.setText(path)
            self.maybe_trigger_preview()

    # ---------- UI-Hilfsfunktionen ----------

    def populate_sketches(self):
        self.sketch_combo.clear()
        for obj in self.doc.Objects:
            if obj.TypeId == "Sketcher::SketchObject":
                self.sketch_combo.addItem(obj.Label, obj.Name)

    def populate_bodies(self):
        self.target_body_combo.clear()
        self.target_body_combo.addItem("<kein Zielkörper>", "")
        for obj in self.doc.Objects:
            if hasattr(obj, "Shape") and obj.Shape.Volume > 0:
                self.target_body_combo.addItem(obj.Label, obj.Name)

    def on_browse_csv(self):
        fn, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.form, "CSV wählen", "", "CSV-Dateien (*.csv);;Alle Dateien (*)"
        )
        if fn:
            self.csv_path_edit.setText(fn)
            self.maybe_trigger_preview()

    def on_browse_font(self):
        fn, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.form,
            "TTF/OTF-Font wählen",
            "",
            "Font-Dateien (*.ttf *.otf);;Alle Dateien (*)"
        )
        if fn:
            self.system_font_combo.setCurrentIndex(0)
            self.font_path_edit.setText(fn)
            self.maybe_trigger_preview()

    def on_load_csv(self):
        path = self.csv_path_edit.text().strip()
        if not path or not os.path.isfile(path):
            QtWidgets.QMessageBox.warning(self.form, "Fehler", "CSV-Datei nicht gefunden.")
            return

        enc = self.encoding_combo.currentText()
        delim = self.delimiter_edit.text() or ";"

        try:
            with open(path, "r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f, delimiter=delim)
                self.csv_rows = list(reader)
                self.csv_headers = reader.fieldnames or []
        except Exception as e:
            QtWidgets.QMessageBox.critical(self.form, "CSV-Fehler", str(e))
            return

        QtWidgets.QMessageBox.information(
            self.form,
            "CSV geladen",
            "Spalten: %s\nZeilen: %d" % (self.csv_headers, len(self.csv_rows)),
        )

        for row in range(self.lines_table.rowCount()):
            combo = self.lines_table.cellWidget(row, 3)
            if isinstance(combo, QtWidgets.QComboBox):
                combo.clear()
                combo.addItems(self.csv_headers)

        self.maybe_trigger_preview()

    def on_scan_lines(self):
        if self.sketch_combo.currentIndex() < 0:
            QtWidgets.QMessageBox.warning(self.form, "Fehler", "Kein Sketch ausgewählt.")
            return

        sketch_name = self.sketch_combo.currentData()
        sk = self.doc.getObject(sketch_name)
        if sk is None:
            QtWidgets.QMessageBox.warning(self.form, "Fehler", "Sketch-Objekt nicht gefunden.")
            return

        geos = sk.Geometry

        lines = []
        for i, g in enumerate(geos):
            if hasattr(g, "StartPoint") and hasattr(g, "EndPoint"):
                if abs(g.StartPoint.y - g.EndPoint.y) < 1e-6:
                    lines.append((i, g))

        self.lines_table.setRowCount(0)

        for idx, (gi, g) in enumerate(lines):
            self.lines_table.insertRow(idx)

            chk = QtWidgets.QTableWidgetItem()
            chk.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            chk.setCheckState(QtCore.Qt.Checked)
            self.lines_table.setItem(idx, 0, chk)

            it_idx = QtWidgets.QTableWidgetItem(str(gi))
            it_idx.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.lines_table.setItem(idx, 1, it_idx)

            y_val = g.StartPoint.y
            it_y = QtWidgets.QTableWidgetItem("%.3f" % y_val)
            it_y.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.lines_table.setItem(idx, 2, it_y)

            col_combo = QtWidgets.QComboBox()
            col_combo.addItems(self.csv_headers)
            col_combo.currentIndexChanged.connect(self.maybe_trigger_preview)
            self.lines_table.setCellWidget(idx, 3, col_combo)

        self.maybe_trigger_preview()

    def get_line_mappings(self):
        mappings = []
        rows = self.lines_table.rowCount()
        for r in range(rows):
            item_active = self.lines_table.item(r, 0)
            if not item_active or item_active.checkState() != QtCore.Qt.Checked:
                continue

            item_geo = self.lines_table.item(r, 1)
            item_y   = self.lines_table.item(r, 2)
            col_combo = self.lines_table.cellWidget(r, 3)

            if not item_geo or not item_y or not col_combo:
                continue

            try:
                geo_index = int(item_geo.text())
                y_line = float(item_y.text())
            except ValueError:
                continue

            csv_col = col_combo.currentText()
            if not csv_col:
                continue

            mappings.append((geo_index, y_line, csv_col))

        return mappings

    def maybe_trigger_preview(self):
        if not self.preview_check.isChecked():
            return
        try:
            if not self.csv_rows or not self.csv_headers:
                return
            if self.sketch_combo.currentIndex() < 0:
                return
            if not self.font_path_edit.text().strip():
                return
            if not self.get_line_mappings():
                return
            self.run_generation(preview=True)
        except Exception as e:
            App.Console.PrintError("Preview-Fehler: %s\n" % e)

    # ---------- Export-Hilfen ----------

    def _get_export_base(self, export_ext):
        """Ermittelt Basisverzeichnis/-namen und räumt alte Exportdateien
        mit der gewählten Erweiterung auf."""
        fc_path = self.doc.FileName
        if not fc_path:
            raise RuntimeError("Dokument ist noch nicht gespeichert. Bitte zuerst speichern.")

        base_dir = os.path.dirname(fc_path)
        fc_name = os.path.splitext(os.path.basename(fc_path))[0]

        export_dir = os.path.join(base_dir, fc_name)

        if not os.path.isdir(export_dir):
            os.makedirs(export_dir, exist_ok=True)
        else:
            # alte Exportdateien mit gleicher Extension löschen
            ext = "." + export_ext.lower()
            for f in os.listdir(export_dir):
                if f.lower().endswith(ext):
                    try:
                        os.remove(os.path.join(export_dir, f))
                    except Exception:
                        pass

        return export_dir, fc_name

    def _sanitize_component(self, text, max_len=None):
        allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
        res = "".join(c if c in allowed else "_" for c in text)
        if max_len and len(res) > max_len:
            res = res[:max_len]
        return res

    def _build_export_path(self, export_dir, fc_name, used_cols, row, export_ext):
        ext = "." + export_ext.lower()
        name_parts = [fc_name]
        for col in used_cols:
            val = (row.get(col) or "").strip()
            if not val:
                continue
            name_parts.append(self._sanitize_component(val))

        base_name = "_".join(name_parts)
        filename = base_name + ext
        full_path = os.path.join(export_dir, filename)

        if len(full_path) <= MAX_PATH_LEN:
            return full_path

        dir_part = export_dir
        reserve = len(dir_part) + 1 + len(ext)
        max_name_len = MAX_PATH_LEN - reserve
        if max_name_len < 1:
            max_name_len = 1

        base_name_short = base_name[:max_name_len]
        filename_short = base_name_short + ext
        full_path_short = os.path.join(dir_part, filename_short)
        return full_path_short

    # ---------- Hauptlogik ----------

    def run_generation(self, preview=False):
        if not self.csv_rows or not self.csv_headers:
            raise RuntimeError("CSV ist nicht geladen.")

        mappings = self.get_line_mappings()
        if not mappings:
            raise RuntimeError("Keine aktiven Hilfslinien-Mappings definiert.")

        font_file = self.font_path_edit.text().strip()
        if not font_file or not os.path.isfile(font_file):
            raise RuntimeError("Font-Datei ist nicht gesetzt oder nicht gefunden.")

        if self.sketch_combo.currentIndex() < 0:
            raise RuntimeError("Kein Sketch ausgewählt.")

        sketch_name = self.sketch_combo.currentData()
        sk = self.doc.getObject(sketch_name)
        if sk is None:
            raise RuntimeError("Sketch-Objekt nicht gefunden.")

        font_scale   = float(self.font_scale_spin.value())
        extrude_h    = float(self.extrude_height_spin.value())
        boolean_mode = self.boolean_mode_combo.currentIndex()
        target_body_name = self.target_body_combo.currentData()
        export_ext = self.export_format_combo.currentData() or "stl"

        # vorhandene Preview-Objekte vor finalem Lauf entfernen
        if not preview and self.preview_objects:
            for obj in list(self.preview_objects):
                if obj in self.doc.Objects:
                    try:
                        self.doc.removeObject(obj.Name)
                    except Exception:
                        pass
            self.preview_objects = []
            self.doc.recompute()

        # Transaktion für finalen Lauf
        if not preview:
            self.doc.openTransaction("CSV_Text_Export")

        # Export-Basis
        if not preview:
            export_dir, fc_name = self._get_export_base(export_ext)
            used_cols = []
            for _, _, col in mappings:
                if col not in used_cols:
                    used_cols.append(col)
        else:
            export_dir, fc_name, used_cols = None, None, None

        # Original-Zielkörper (wird pro CSV-Zeile kopiert)
        orig_target_body = None
        if not preview and boolean_mode == 1:
            if not target_body_name:
                raise RuntimeError("Fuse-Modus gewählt, aber kein Zielkörper ausgewählt.")
            orig_target_body = self.doc.getObject(target_body_name)
            if orig_target_body is None:
                raise RuntimeError("Zielkörper nicht gefunden.")

        bbox_sk = sk.Shape.BoundBox
        z_offset = float(bbox_sk.ZMin)

        geos = sk.Geometry
        y_vals = [m[1] for m in mappings]
        if len(y_vals) >= 2:
            y_top = max(y_vals)
            y_bottom = min(y_vals)
            vertical_height = abs(y_top - y_bottom)
        else:
            vertical_height = 10.0

        text_size = vertical_height * font_scale

        App.Console.PrintMessage(
            "font_scale=%.3f, text_size=%.3f, preview=%s\n"
            % (font_scale, text_size, preview)
        )

        # alte Preview-Objekte im Preview-Modus löschen
        if preview and self.preview_objects:
            for obj in list(self.preview_objects):
                if obj in self.doc.Objects:
                    try:
                        self.doc.removeObject(obj.Name)
                    except Exception:
                        pass
            self.preview_objects = []
            self.doc.recompute()

        def make_and_place_text(value, geo_index, y_line):
            g = geos[geo_index]
            x1 = g.StartPoint.x
            x2 = g.EndPoint.x
            x_center = 0.5 * (x1 + x2)

            if not value:
                return None

            ss = Draft.makeShapeString(
                String=value,
                FontFile=font_file,
                Size=text_size,
                Tracking=0
            )

            ss.Placement.Base = App.Vector(x1, y_line, z_offset)
            self.doc.recompute()

            bbox = ss.Shape.BoundBox
            width = float(bbox.XLength)
            ymid  = 0.5 * (float(bbox.YMin) + float(bbox.YMax))

            ss.Placement.Base.x = x_center - width / 2.0
            dy = y_line - ymid
            ss.Placement.Base.y += dy

            self.doc.recompute()
            return ss

        def extrude_text(ss_obj):
            if ss_obj is None:
                return None
            ext = self.doc.addObject("Part::Extrusion", "TextExtrude")
            ext.Base = ss_obj
            ext.Dir = App.Vector(0, 0, extrude_h)
            ext.Solid = True
            ext.TaperAngle = 0
            self.doc.recompute()
            return ext

        if preview:
            rows_to_process = self.csv_rows[:1]
        else:
            rows_to_process = self.csv_rows

        # Fortschrittsdialog nur im finalen Modus
        progress = None
        if not preview:
            total = len(rows_to_process)
            progress = QtWidgets.QProgressDialog(
                "Export läuft…", "Abbrechen", 0, total
            )
            progress.setWindowModality(QtCore.Qt.WindowModal)
            progress.setMinimumDuration(0)

        for row_idx, row in enumerate(rows_to_process):
            # Fortschritt aktualisieren
            if progress is not None:
                progress.setValue(row_idx)
                progress.setLabelText(
                    f"Exportiere {row_idx + 1} / {len(rows_to_process)}"
                )
                QtWidgets.QApplication.processEvents()
                if progress.wasCanceled():
                    break

            App.Console.PrintMessage(
                "CSV-Zeile %d (%s)\n" % (row_idx, "Preview" if preview else "Final")
            )
            new_extrudes = []

            for (geo_index, y_line, csv_col) in mappings:
                if csv_col not in row:
                    continue
                value = (row.get(csv_col) or "").strip()
                ss = make_and_place_text(value, geo_index, y_line)
                ext = extrude_text(ss)
                if ext:
                    new_extrudes.append(ext)
                    if preview:
                        self.preview_objects.extend([ss, ext])

            # Per-Zeile-Fuse: für jede CSV-Zeile eine eigene Kopie des Zielkörpers
            if not preview and boolean_mode == 1 and orig_target_body is not None:
                base_copy = self.doc.copyObject(orig_target_body, True)
                current = base_copy
                for ext in new_extrudes:
                    fuse = self.doc.addObject("Part::Fuse", "TextFuse")
                    fuse.Base = current
                    fuse.Tool = ext
                    self.doc.recompute()
                    current.ViewObject.Visibility = False
                    current = fuse

                export_obj_list = [current]
            else:
                export_obj_list = new_extrudes

            if not preview and export_obj_list:
                export_path = self._build_export_path(export_dir, fc_name, used_cols, row, export_ext)

                if os.path.exists(export_path):
                    try:
                        os.remove(export_path)
                    except Exception:
                        pass

                try:
                    ext = export_ext.lower()

                    # STL und 3MF über Mesh.export, STEP u.a. über ImportGui.export
                    if ext in ("stl", "3mf"):
                        Mesh.export(export_obj_list, export_path)
                    else:
                        ImportGui.export(export_obj_list, export_path)

                    App.Console.PrintMessage("Exportiert: %s\n" % export_path)
                except Exception as e:
                    App.Console.PrintError(
                        "Exportfehler (%s) bei '%s': %s\n"
                        % (export_ext, export_path, e)
                    )

        # Fortschrittsdialog abschließen
        if not preview and progress is not None:
            progress.setValue(len(rows_to_process))

        if not preview:
            QtWidgets.QMessageBox.information(
                self.form,
                "Fertig",
                "Texte wurden erzeugt, extrudiert und exportiert.\n"
                "Boolean-Fuse ggf. mit Zielkörper ausgeführt.",
            )
        else:
            App.Console.PrintMessage("Preview aktualisiert.\n")

        # nach finalem Lauf alle Modelländerungen verwerfen → Ursprungszustand
        if not preview:
            try:
                self.doc.abortTransaction()
            except Exception:
                pass
            self.doc.recompute()

class CSV2ObjectsCmd:
    def GetResources(self):
        # Icon-Pfad für das Kommando (Toolbar/Menu)
        base_dir = os.path.join(
            App.getUserAppDataDir(),
            "Mod",
            "CSV2Objects",
            "resources",
            "icons",
        )
        svg_path = os.path.join(base_dir, "CSV2Objects.svg")
        png_path = os.path.join(base_dir, "CSV2Objects.png")

        pixmap = ""
        if os.path.exists(svg_path):
            pixmap = svg_path
        elif os.path.exists(png_path):
            pixmap = png_path

        return {
            "MenuText": "CSV2Objects",
            "ToolTip": (
                "Erzeugt massenhaft 3D-Objekte mit Text aus CSV-Dateien."
            ),
            "Pixmap": pixmap,
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        """Wird beim Klick auf das Toolbar-/Menü-Icon ausgeführt.

        Öffnet einen neuen CSV2Objects-TaskPanel.
        """
        panel = TextFromCSVTaskPanel()
        Gui.Control.showDialog(panel)


def register_commands():
    """
    Registriert die CSV2Objects-Kommandos bei FreeCAD.
    Wird von InitGui.py aufgerufen.
    """
    Gui.addCommand("CSV2Objects_Run", CSV2ObjectsCmd())