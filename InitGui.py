import os
import FreeCAD as App
import FreeCADGui as Gui

# Log load to help diagnose workbench visibility
App.Console.PrintMessage("CSV2Objects: InitGui.py loaded.\n")


class CSV2ObjectsWorkbench(Gui.Workbench):
    """
    Workbench for CSV2Objects.
    Provides a 'CSV2Objects_Run' command in the toolbar and menu.
    """

    MenuText = "CSV2Objects"
    ToolTip = "Generate large batches of 3D objects with text from CSV files."

    def __init__(self):
        # Icon: prefer SVG, then fall back to PNG
        # Robust base directory resolution (some FreeCAD contexts may not define __file__)
        try:
            base_dir = os.path.dirname(__file__)
        except Exception:
            # Fallback: user Mod path
            base_dir = os.path.join(App.getUserAppDataDir(), "Mod", "CSV2Objects")

        base_dir = os.path.abspath(base_dir)
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
        # Import CSV2Objects GUI module (local import to avoid init issues)
        try:
            import CSV2ObjectsGui
        except Exception as e:
            App.Console.PrintError("CSV2Objects: failed to import CSV2ObjectsGui: %s\n" % e)
            raise
        # Register commands
        CSV2ObjectsGui.register_commands()

        cmd_list = ["CSV2Objects_Run"]

        # Add toolbar and menu
        self.appendToolbar("CSV2Objects", cmd_list)
        self.appendMenu("CSV2Objects", cmd_list)

        App.Console.PrintMessage("CSV2ObjectsWorkbench: initialized.\n")

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(CSV2ObjectsWorkbench())
