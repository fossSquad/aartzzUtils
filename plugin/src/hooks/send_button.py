from base_plugin import MethodHook
from hook_utils import find_class, get_private_field, set_private_field

class GetThemedColorHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin
        try:
            self.ThemeClass = find_class("org.telegram.ui.ActionBar.Theme")
            self.key_chat_messagePanelSend = getattr(self.ThemeClass, "key_chat_messagePanelSend")
            self.ThreadClass = find_class("java.lang.Thread")
        except Exception:
            self.ThemeClass = None
            self.key_chat_messagePanelSend = None
            self.ThreadClass = None

    def after_hooked_method(self, param):
        if not self.setting_hide_bg:
            return
            
        try:
            if param.args[0] == self.key_chat_messagePanelSend:
                stack = self.ThreadClass.currentThread().getStackTrace()
                for i in range(min(15, len(stack))):
                    element = stack[i]
                    if element.getMethodName() == "dispatchDraw" and "ChatActivityEnterView" in element.getClassName():
                        message_edit_text = get_private_field(param.thisObject, "messageEditText")
                        if message_edit_text is not None:
                            text = message_edit_text.getText()
                            if text is not None and text.length() > 0:
                                return
                        param.setResult(0)
                        return
        except Exception:
            return

class SendButtonOnDrawHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin
        self.setting_hide_bg = self.plugin.get_setting("hide_send_button_bg", False)
        self.setting_legacy_icons = self.plugin.get_setting("legacy_outline_icons", True)
        try:
            self.SendButtonClass = find_class("org.telegram.ui.Components.ChatActivityEnterView$SendButton")
        except Exception:
            return

    def get_target_class(self):
        return "org.telegram.ui.Components.ChatActivityEnterView$SendButton"

    def get_target_method(self):
        return "onDraw"

    def before_hooked_method(self, param):
        if not self.setting_hide_bg:
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
                    
                    if self.setting_legacy_icons:
                        drawable = get_private_field(param.thisObject, "drawable")
                        micDrawable = get_private_field(outer, "micDrawable")
                        cameraDrawable = get_private_field(outer, "cameraDrawable")
                        
                        if drawable is not None:
                            if micDrawable is not None and drawable == micDrawable:
                                micOutline = get_private_field(outer, "micOutline")
                                if micOutline is not None:
                                    set_private_field(param.thisObject, "drawable", micOutline)
                                    self.old_drawable = micDrawable
                            elif cameraDrawable is not None and drawable == cameraDrawable:
                                cameraOutline = get_private_field(outer, "cameraOutline")
                                if cameraOutline is not None:
                                    set_private_field(param.thisObject, "drawable", cameraOutline)
                                    self.old_drawable = cameraDrawable
                else:
                    self.old_color = None
                    self.old_drawable = None
            else:
                self.old_color = None
                self.old_drawable = None
        except Exception:
            self.old_color = None
            self.old_drawable = None

    def after_hooked_method(self, param):
        if getattr(self, "old_color", None) is not None:
            try:
                paint = get_private_field(param.thisObject, "backgroundPaint")
                if paint:
                    paint.setColor(self.old_color)
            except Exception:
                pass
                
        if getattr(self, "old_drawable", None) is not None:
            try:
                set_private_field(param.thisObject, "drawable", self.old_drawable)
            except Exception:
                pass

class ChatActivityEnterViewUpdateColorsHook(MethodHook):
    def __init__(self, plugin):
        pass
    def after_hooked_method(self, param):
        pass
