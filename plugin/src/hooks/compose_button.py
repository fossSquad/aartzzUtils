from base_plugin import MethodHook
from hook_utils import find_class, get_private_field


class ComposeButtonHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin
        self._pencil_id = None
        self._pencil_checked = False

    def _get_pencil_id(self):
        if not self._pencil_checked:
            self._pencil_checked = True
            R_drawable = find_class("org.telegram.messenger.R$drawable")
            if R_drawable is not None:
                self._pencil_id = getattr(R_drawable, "floating_pencil", None)
        return self._pencil_id

    def after_hooked_method(self, param):
        if not self.plugin.get_setting("compose_pencil", False):
            return

        pencil_id = self._get_pencil_id()
        if pencil_id is None:
            return

        try:
            button = get_private_field(param.thisObject, "floatingButton3")
            if button is not None:
                button.setImageResource(pencil_id)
        except Exception:
            pass
