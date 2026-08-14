from base_plugin import MethodHook

class LaunchActivityNavBarColorHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin

    def before_hooked_method(self, param):
        # Force navigation bar to be completely transparent so the app background shows through
        # This is required because if padding=0, the blurred bottom panel covers the nav bar,
        # and we need the system nav bar to be transparent so the blur is visible.
        from java.lang import Integer
        param.args[0] = Integer(0)
