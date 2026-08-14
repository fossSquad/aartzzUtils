from base_plugin import MethodHook
from hook_utils import get_private_field, set_private_field


class CameraTileSingleCellHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin

    def after_hooked_method(self, param):
        if not self.plugin.get_setting("camera_tile_single_cell", False):
            return

        try:
            adapter = param.thisObject
            has_spacer = bool(get_private_field(adapter, "hasCameraSpaceRow"))
            if not has_spacer:
                return

            set_private_field(adapter, "hasCameraSpaceRow", False)
            items_count = int(get_private_field(adapter, "itemsCount"))
            if items_count > 0:
                set_private_field(adapter, "itemsCount", items_count - 1)
                param.setResult(int(param.getResult()) - 1)
        except Exception:
            pass
