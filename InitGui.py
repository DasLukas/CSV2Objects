import os
import FreeCAD as App
import FreeCADGui as Gui


class CSV2ObjectsWorkbench(Gui.Workbench):
    """
    Workbench für CSV2Objects.
    Stellt ein Kommando 'CSV2Objects_Run' in Toolbar und Menü bereit.
    """

    MenuText = "CSV2Objects"
    ToolTip = "Erzeuge massenhaft 3D-Objekte mit Text aus CSV-Dateien."

    def __init__(self):
        # Icon: zuerst SVG, dann PNG versuchen
        # Basisverzeichnis über den Mod-Pfad ermitteln (CSV2Objects liegt unter Mod/CSV2Objects)
        base_dir = os.path.join(App.getUserAppDataDir(), "Mod", "CSV2Objects")
        icon_dir = os.path.join(base_dir, "resources", "icons")
        svg_path = os.path.join(icon_dir, "CSV2Objects.svg")
        png_path = os.path.join(icon_dir, "CSV2Objects.png")

        if os.path.exists(svg_path):
            self.Icon = svg_path
        elif os.path.exists(png_path):
            self.Icon = png_path
        else:
            self.Icon = ""

    def Initialize(self):
        # CSV2Objects-GUI-Modul importieren (lokaler Import, um Initialisierungsprobleme zu vermeiden)
        import CSV2ObjectsGui
        # Kommandos registrieren
        CSV2ObjectsGui.register_commands()

        cmd_list = ["CSV2Objects_Run"]

        # Toolbar und Menü hinzufügen
        self.appendToolbar("CSV2Objects", cmd_list)
        self.appendMenu("CSV2Objects", cmd_list)

        App.Console.PrintMessage("CSV2ObjectsWorkbench: initialisiert.\n")

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(CSV2ObjectsWorkbench())