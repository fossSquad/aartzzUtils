from base_plugin import MethodHook
from hook_utils import get_private_field


class SettingsIconsHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin

    def after_hooked_method(self, param):
        if not self.plugin.get_setting("legacy_settings_icons", False):
            return

        try:
            background = get_private_field(param.thisObject, "iconBackground")
            if background is None:
                return

            from java.lang import Boolean
            try:
                background.setColor(0, 0, Boolean(False))
            except Exception:
                background.setColor(0, 0)
        except Exception:
            pass
