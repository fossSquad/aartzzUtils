from base_plugin import MethodHook
from hook_utils import get_private_field


class ProfileLevelsHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin

    def after_hooked_method(self, param):
        if not self.plugin.get_setting("hide_profile_levels", False):
            return

        try:
            rating_view = get_private_field(param.thisObject, "ratingView")
            if rating_view is not None:
                rating_view.setVisibility(8)
        except Exception:
            pass
