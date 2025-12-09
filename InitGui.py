import os
import FreeCAD as App
import FreeCADGui as Gui

from . import CSV2ObjectsGui


class CSV2ObjectsWorkbench(Gui.Workbench):
    """
    Workbench für CSV2Objects.
    Stellt ein Kommando 'CSV2Objects_Run' in Toolbar und Menü bereit.
    """

    MenuText = "CSV2Objects"
    ToolTip = "Erzeuge massenhaft 3D-Objekte mit Text aus CSV-Dateien."

    def __init__(self):
        icon_path = os.path.join(
            os.path.dirname(__file__),
            "resources",
            "icons",
            "CSV2Objects.svg"
        )
        if os.path.exists(icon_path):
            self.Icon = icon_path
        else:
            self.Icon = ""

    def Initialize(self):
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