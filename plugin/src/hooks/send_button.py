from base_plugin import MethodHook
from hook_utils import find_class, get_private_field

class GetThemedColorHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin
        try:
            self.ThemeClass = find_class("org.telegram.ui.ActionBar.Theme")
            self.key_chat_messagePanelSend = getattr(self.ThemeClass, "key_chat_messagePanelSend")
            self.ThreadClass = find_class("java.lang.Thread")
        except Exception as e:

    def after_hooked_method(self, param):
        if not self.plugin.get_setting("hide_send_button_bg", False):
            return
            
        try:
            if param.args[0] == self.key_chat_messagePanelSend:
                stack = self.ThreadClass.currentThread().getStackTrace()
                for i in range(min(15, len(stack))):
                    element = stack[i]
                    if element.getMethodName() == "dispatchDraw" and "ChatActivityEnterView" in element.getClassName():
                        param.setResult(0) # 0 is transparent color
                        return
        except Exception as e:

class SendButtonOnDrawHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin
        try:
            self.SendButtonClass = find_class("org.telegram.ui.Components.ChatActivityEnterView$SendButton")
        except Exception as e:

    def get_target_class(self):
        return "org.telegram.ui.Components.ChatActivityEnterView$SendButton"

    def get_target_method(self):
        return "onDraw"

    def before_hooked_method(self, param):
        if not self.plugin.get_setting("hide_send_button_bg", False):
            return

        try:
            if not getattr(self, "logged_dir", False):
                self.logged_dir = True

            # SendButton is static, so it doesn't have this$0. We traverse parents.
            view = param.thisObject
            parent = view.getParent()
            outer = None
            while parent:
                if "ChatActivityEnterView" in parent.getClass().getName() and "$" not in parent.getClass().getName():
                    outer = parent
                    break
                parent = parent.getParent()
                
            if not outer:
                return
            
            messageEditText = get_private_field(outer, "messageEditText")
            if messageEditText:
                text = messageEditText.getText().toString()
                
                if not text:
                    paint = get_private_field(param.thisObject, "backgroundPaint")
                    if paint:
                        self.old_color = paint.getColor()
                        paint.setColor(0) # transparent
                else:
                    self.old_color = None
            else:
        except Exception as e:
            self.old_color = None

    def after_hooked_method(self, param):
        if getattr(self, "old_color", None) is not None:
            try:
                paint = get_private_field(param.thisObject, "backgroundPaint")
                if paint:
                    paint.setColor(self.old_color)
            except Exception as e:
                pass

class ChatActivityEnterViewUpdateColorsHook(MethodHook):
    def __init__(self, plugin):
        pass
    def after_hooked_method(self, param):
        pass
