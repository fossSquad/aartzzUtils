from base_plugin import MethodHook
from hook_utils import find_class, get_private_field


class ComposeButtonHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin
        self.theme = find_class("org.telegram.ui.ActionBar.Theme")

    def after_hooked_method(self, param):
        if not self.plugin.get_setting("compose_pencil", True):
            return

        try:
            button = get_private_field(param.thisObject, "floatingButton3")
            if button is not None:
                R_drawable = find_class("org.telegram.messenger.R$drawable")
                pencil_id = getattr(R_drawable, "floating_pencil", None)
                if pencil_id is not None:
                    button.setImageResource(pencil_id)
        except Exception:
            pass
