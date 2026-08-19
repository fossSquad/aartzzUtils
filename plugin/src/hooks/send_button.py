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
        if not self.plugin.get_setting("hide_send_button_bg", False):
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
        try:
            self.SendButtonClass = find_class("org.telegram.ui.Components.ChatActivityEnterView$SendButton")
        except Exception:
            return

    def get_target_class(self):
        return "org.telegram.ui.Components.ChatActivityEnterView$SendButton"

    def get_target_method(self):
        return "onDraw"

    def before_hooked_method(self, param):
        hide_bg = self.plugin.get_setting("hide_send_button_bg", False)
        legacy_icons = self.plugin.get_setting("legacy_outline_icons", False)
        if not hide_bg and not legacy_icons:
            return

        try:
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
                    if hide_bg:
                        paint = get_private_field(param.thisObject, "backgroundPaint")
                        if paint:
                            self.old_color = paint.getColor()
                            paint.setColor(0)
                    
                    if legacy_icons:
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

class SendButtonUpdateColorsHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin

    def after_hooked_method(self, param):
        if not hasattr(self, "_fired_logged"):
            self._fired_logged = True
            self.plugin.log("[sendbtn] updateColors FIRED (first time)")
        if not self.plugin.get_setting("hide_send_button_bg", False):
            return
        try:
            view = param.thisObject
            self.plugin.log("[sendbtn] updateColors hooked, setting on")
            parent = view.getParent()
            outer = None
            while parent:
                if "ChatActivityEnterView" in parent.getClass().getName() and "$" not in parent.getClass().getName():
                    outer = parent
                    break
                parent = parent.getParent()
            if not outer:
                self.plugin.log("[sendbtn] outer ChatActivityEnterView not found")
                return
            edit = get_private_field(outer, "messageEditText")
            if edit is not None:
                text = edit.getText()
                if text is not None and text.length() > 0:
                    self.plugin.log("[sendbtn] text non-empty, keeping bg")
                    return
            paint = get_private_field(view, "backgroundPaint")
            if paint is not None:
                before = paint.getColor()
                paint.setColor(0)
                self.plugin.log(f"[sendbtn] backgroundPaint color {before} -> 0")
            else:
                self.plugin.log("[sendbtn] backgroundPaint is None")
        except Exception as e:
            self.plugin.log(f"[sendbtn] updateColors hook error: {e}")


class ChatActivityEnterViewUpdateColorsHook(MethodHook):
    def __init__(self, plugin):
        pass
    def after_hooked_method(self, param):
        pass


class AudioVideoOutlineHook(MethodHook):
    """Hides the circular outline behind the voice/video (mic/camera) button.

    The real button is ChatActivityEnterView.audioVideoSendButton — an
    anonymous view (ChatActivityEnterView$25 with the base icon pack,
    $26 with legacy outline icons). Both override draw(Canvas): they paint
    the outline drawable (outer.micOutline / outer.cameraOutline) and return
    early. Instead of intercepting every draw() call (a reflective invoke
    through the Python/Java bridge per frame was both slow and unreliable),
    we swap the OUTER's outline drawables for the plain mic/camera glyphs
    ONCE. The fields are only written in the outer's <init>, so the swap
    persists and the built-in draw() renders the bare glyph with zero
    per-frame hook cost.
    """

    def __init__(self, plugin):
        self.plugin = plugin
        self._done = set()

    def before_hooked_method(self, param):
        try:
            if not self.plugin.get_setting("hide_send_button_bg", False):
                return
            view = param.thisObject
            vid = hash(view)
            if vid in self._done:
                return
            outer = get_private_field(view, "this$0")
            if outer is not None:
                for outline_name, plain_name in (
                    ("micOutline", "micDrawable"),
                    ("cameraOutline", "cameraDrawable"),
                ):
                    plain = get_private_field(outer, plain_name)
                    if plain is not None:
                        set_private_field(outer, outline_name, plain)
                self.plugin.log("[outline] swapped outline drawables for plain icons")
            self._done.add(vid)
        except Exception as e:
            self.plugin.log(f"[outline] swap error: {e}")
