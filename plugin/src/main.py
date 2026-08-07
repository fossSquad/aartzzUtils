from elyx import strings
from base_plugin import BasePlugin
from java.lang import Class as JavaClass

from .hooks import IsBasePackOnlyHook, DialogCellOnDrawHook, DialogCellBuildLayoutHook
from .ui import SettingsMixin

class ExteraRestorePlugin(SettingsMixin, BasePlugin):
    def on_plugin_load(self):
        self.log(strings("loaded"))

        # 1. Hook IconManager
        IconManagerClass = JavaClass.forName("com.exteragram.messenger.icons.IconManager")
        IconPackTypeClass = JavaClass.forName("com.exteragram.messenger.IconPackType")
        if IconManagerClass and IconPackTypeClass:
            try:
                is_base_pack_only_method = IconManagerClass.getDeclaredMethod("isBasePackOnly", IconPackTypeClass)
                is_base_pack_only_method.setAccessible(True)
                self.hook_method(is_base_pack_only_method, IsBasePackOnlyHook(self))
                self.log("Hooked IconManager.isBasePackOnly")
            except Exception as e:
                self.log(f"Failed to hook IconManager: {e}")

        # 2. Hook DialogCell.onDraw
        DialogCellClass = JavaClass.forName("org.telegram.ui.Cells.DialogCell")
        if DialogCellClass:
            # Hook buildLayout to fix date spacing
            self.hook_all_methods(DialogCellClass, "buildLayout", DialogCellBuildLayoutHook(self))
            
            # Hook onDraw to handle drawing legacy highlight and pin
            hooked = self.hook_all_methods(DialogCellClass, "onDraw", DialogCellOnDrawHook(self))
            if hooked:
                self.log("Hooked DialogCell.onDraw")
            else:
                self.log("Failed to hook DialogCell.onDraw")
