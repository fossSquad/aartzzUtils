from base_plugin import MethodHook
from hook_utils import get_private_field


class SettingsIconsHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin

    def after_hooked_method(self, param):
        if not self.plugin.get_setting("legacy_settings_icons", False):
            return

        try:
            this = param.thisObject
            icon_layout = get_private_field(this, "iconLayout")
            if icon_layout is not None:
                icon_layout.setBackground(None)

            background = get_private_field(this, "iconBackground")
            if background is not None:
                from java.lang import Boolean
                try:
                    background.setColor(0, 0, Boolean(False))
                except Exception:
                    background.setColor(0, 0)
                    
            icon_view = get_private_field(this, "iconView")
            if icon_view is not None:
                # No color filter here: any SRC_IN tint overrides the app's own
                # native icon tint (white on dark themes) and goes stale on
                # recycled cells (dark-blue in scrolled-out rows). Let the app
                # tint the icon itself; we only neutralize the colored
                # background and center the icon.
                from org.telegram.ui.Components import LayoutHelper
                from android.view import Gravity
                icon_view.setLayoutParams(LayoutHelper.createFrame(28, 28, Gravity.CENTER))
        except Exception:
            pass
