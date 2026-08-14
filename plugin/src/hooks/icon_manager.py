from base_plugin import MethodHook
from java.lang import Thread

class IsBasePackOnlyHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin

    def before_hooked_method(self, param):
        if not self.plugin.get_setting("legacy_outline_icons", False):
            return
            
        stack = Thread.currentThread().getStackTrace()
        for element in stack:
            if "ChatActivityEnterView" in element.getClassName():
                param.setResult(True)
                return
