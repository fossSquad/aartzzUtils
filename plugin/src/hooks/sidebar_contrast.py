from base_plugin import MethodHook


class ImmersiveDrawerHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin

    def before_hooked_method(self, param):
        if self.plugin.get_setting("sidebar_contrast", True):
            param.setResult(False)
