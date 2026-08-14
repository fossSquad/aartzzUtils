from collections import OrderedDict
from base_plugin import MethodHook
from hook_utils import find_class

class _FieldCache:
    def __init__(self):
        self.fields = {}
        self.missing = set()

    def _resolve(self, java_class, name):
        key = (java_class, name)
        field = self.fields.get(key)
        if field is not None:
            return field
        if key in self.missing:
            return None

        current = java_class
        while current is not None:
            try:
                field = current.getDeclaredField(name)
                field.setAccessible(True)
                self.fields[key] = field
                return field
            except Exception:
                current = current.getSuperclass()
        self.missing.add(key)
        return None

    def get(self, instance, name, default=None):
        try:
            field = self._resolve(instance.getClass(), name)
            return default if field is None else field.get(instance)
        except Exception:
            return default

    def set(self, instance, name, value):
        try:
            field = self._resolve(instance.getClass(), name)
            if field is not None:
                field.set(instance, value)
                return True
        except Exception:
            pass
        return False

def _java_identity(instance):
    return hash(instance)

class _BoundedState:
    def __init__(self, limit=256):
        self.limit = limit
        self.values = OrderedDict()

    def get(self, key, default=None):
        value = self.values.get(key, default)
        if key in self.values:
            self.values.move_to_end(key)
        return value

    def set(self, key, value):
        self.values[key] = value
        self.values.move_to_end(key)
        while len(self.values) > self.limit:
            self.values.popitem(last=False)

    def pop(self, key, default=None):
        return self.values.pop(key, default)

_SHARED_LAYOUT_CACHE = _BoundedState(256)

class DialogCellBuildLayoutHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin
        self.alpha_hidden_map = _BoundedState()
        self.fields = _FieldCache()
        self.ThemeProxy = find_class("org.telegram.ui.ActionBar.Theme")
        self.AndroidUtilities = find_class("org.telegram.messenger.AndroidUtilities")

    def before_hooked_method(self, param):
        this = param.thisObject
        cell_id = _java_identity(this)
        original_flags = (False, False)
        
        try:
            dp = self.fields.get(this, "drawPin", False)
            dpf = self.fields.get(this, "drawPinForced", False)
            
            is_pinned = bool(dp) or bool(dpf)
            original_flags = (bool(dp), bool(dpf))
            
            if is_pinned and self.plugin.get_setting("legacy_pin_pos", True):
                self.fields.set(this, "drawPin", False)
                self.fields.set(this, "drawPinForced", False)
                self.alpha_hidden_map.set(cell_id, original_flags)
        except Exception:
            pass
        finally:
            if self.alpha_hidden_map.get(cell_id) is None:
                self.alpha_hidden_map.set(cell_id, original_flags)

    def after_hooked_method(self, param):
        this = param.thisObject
        cell_id = _java_identity(this)
        original_flags = self.alpha_hidden_map.pop(cell_id, (False, False))

        if original_flags != (False, False):
            try:
                self.fields.set(this, "drawPin", original_flags[0])
                self.fields.set(this, "drawPinForced", original_flags[1])
            except Exception:
                pass

        is_pinned = original_flags[0] or original_flags[1]
        if not is_pinned or not self.plugin.get_setting("legacy_pin_pos", True):
            _SHARED_LAYOUT_CACHE.pop(cell_id, None)
            return

        try:
            ThemeProxy = self.ThemeProxy
            AndroidUtilities = self.AndroidUtilities

            unread_count = 0
            mark_unread = False
            try:
                unread_count = int(self.fields.get(this, "unreadCount", 0))
            except Exception:
                pass
            try:
                mark_unread = bool(self.fields.get(this, "markUnread", False))
            except Exception:
                pass

            if self.plugin.get_setting("hide_pin_if_unread", False) and (unread_count != 0 or mark_unread):
                _SHARED_LAYOUT_CACHE.pop(cell_id, None)
                return

            draw_count = False
            is_muted = False
            try:
                draw_count = bool(self.fields.get(this, "drawCount", False))
            except Exception:
                pass
            try:
                is_muted = bool(this.isCounterMuted())
            except Exception:
                pass

            if draw_count and not is_muted:
                pin_drawable = ThemeProxy.dialogs_pinnedDrawable2Accent
            else:
                pin_drawable = ThemeProxy.dialogs_pinnedDrawable2
            if pin_drawable is None:
                pin_drawable = ThemeProxy.dialogs_pinnedDrawable
            if pin_drawable is None:
                _SHARED_LAYOUT_CACHE.pop(cell_id, None)
                return

            icon_w = pin_drawable.getIntrinsicWidth()
            icon_h = pin_drawable.getIntrinsicHeight()
            measured_w = this.getMeasuredWidth()

            try:
                count_top = int(self.fields.get(this, "countTop"))
            except Exception:
                count_top = AndroidUtilities.dp(39.0)

            pin_top = count_top + (AndroidUtilities.dp(20.0) - icon_h) // 2

            if unread_count != 0 or mark_unread or draw_count:
                try:
                    count_left = int(self.fields.get(this, "countLeft"))
                    pin_left = count_left - icon_w - AndroidUtilities.dp(6.0)
                except Exception:
                    pin_left = measured_w - icon_w - AndroidUtilities.dp(14.0)
            else:
                pin_left = measured_w - icon_w - AndroidUtilities.dp(14.0)

            badge_gap = AndroidUtilities.dp(6.0)
            if bool(self.fields.get(this, "drawReactionMention", False)):
                reaction_left = self.fields.get(this, "reactionMentionLeft")
                if reaction_left is not None:
                    pin_left = min(pin_left, int(reaction_left) - icon_w - badge_gap)
            if bool(self.fields.get(this, "drawPollVotesMention", False)):
                poll_left = self.fields.get(this, "pollVotesMentionLeft")
                if poll_left is not None:
                    pin_left = min(pin_left, int(poll_left) - icon_w - badge_gap)
            if bool(self.fields.get(this, "drawMention", False)):
                mention_left = self.fields.get(this, "mentionLeft")
                if mention_left is not None:
                    pin_left = min(pin_left, int(mention_left) - icon_w - badge_gap)
            if bool(self.fields.get(this, "drawError", False)):
                error_left = self.fields.get(this, "errorLeft")
                if error_left is not None:
                    pin_left = min(pin_left, int(error_left) - icon_w - badge_gap)

            _SHARED_LAYOUT_CACHE.set(cell_id, (pin_left, pin_top, icon_w, icon_h, pin_drawable))
        except Exception as e:
            self.plugin.log(f"[buildLayout after] {e}")


class DialogCellOnDrawHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin
        self.state_map = _BoundedState()
        self.fields = _FieldCache()
        self.ThemeProxy = find_class("org.telegram.ui.ActionBar.Theme")
        self.key_chats_pinnedOverlay = getattr(self.ThemeProxy, "key_chats_pinnedOverlay", None)
        try:
            from android.graphics import Paint
            self.bg_paint = Paint()
        except Exception:
            self.bg_paint = None
        
        self.setting_legacy_pin_pos = self.plugin.get_setting("legacy_pin_pos", True)
        self.setting_pinned_bg = self.plugin.get_setting("pinned_bg", True)
        
        try:
            DialogCellClass = find_class("org.telegram.ui.Cells.DialogCell")
            self.f_drawPin = DialogCellClass.getDeclaredField("drawPin")
            self.f_drawPin.setAccessible(True)
            self.f_drawPinForced = DialogCellClass.getDeclaredField("drawPinForced")
            self.f_drawPinForced.setAccessible(True)
            self.f_isTopic = DialogCellClass.getDeclaredField("isTopic")
            self.f_isTopic.setAccessible(True)
            self.f_resourcesProvider = DialogCellClass.getDeclaredField("resourcesProvider")
            self.f_resourcesProvider.setAccessible(True)
        except Exception:
            self.f_drawPin = None
            self.f_drawPinForced = None
            self.f_isTopic = None
            self.f_resourcesProvider = None

    def _get_f(self, field, this, default):
        if field is None: return default
        try:
            return field.get(this)
        except Exception:
            return default

    def _set_f(self, field, this, value):
        if field is not None:
            try:
                field.set(this, value)
            except Exception:
                pass

    def before_hooked_method(self, param):
        this = param.thisObject
        cell_id = _java_identity(this)
        original_flags = (False, False)
        is_pinned = False
        is_topic = False
        
        try:
            dp = self._get_f(self.f_drawPin, this, False)
            dpf = self._get_f(self.f_drawPinForced, this, False)
            is_topic = self._get_f(self.f_isTopic, this, False)
            
            is_pinned = bool(dp) or bool(dpf)
            original_flags = (bool(dp), bool(dpf))

            if is_pinned and self.setting_pinned_bg:
                try:
                    canvas = param.args[0]
                    color = None
                    try:
                        rp = self._get_f(self.f_resourcesProvider, this, None)
                        if self.key_chats_pinnedOverlay is not None:
                            color = self.ThemeProxy.getColor(self.key_chats_pinnedOverlay, rp)
                    except Exception:
                        pass
                        
                    if color is None and self.key_chats_pinnedOverlay is not None:
                        try:
                            color = self.ThemeProxy.getColor(self.key_chats_pinnedOverlay)
                        except Exception:
                            pass
                            
                    if color is not None:
                        self.bg_paint.setColor(color)
                        self.bg_paint.setAlpha(15)
                        canvas.drawRect(0.0, 0.0, float(this.getMeasuredWidth()), float(this.getMeasuredHeight()), self.bg_paint)
                except Exception:
                    pass

            if is_pinned and self.setting_legacy_pin_pos:
                try:
                    self._set_f(self.f_drawPin, this, False)
                    self._set_f(self.f_drawPinForced, this, False)
                except Exception as e:
                    self.plugin.log(f"drawPin hide error: {e}")

        except Exception as e:
            self.plugin.log(f"[before] {e}")
        finally:
            self.state_map.set(cell_id, (is_pinned, original_flags))

    def after_hooked_method(self, param):
        this = param.thisObject
        canvas = param.args[0]
        cell_id = _java_identity(this)
        state = self.state_map.pop(cell_id, (False, (False, False)))
        is_pinned, original_flags = state

        if original_flags != (False, False):
            try:
                self._set_f(self.f_drawPin, this, original_flags[0])
                self._set_f(self.f_drawPinForced, this, original_flags[1])
            except Exception:
                pass

        if not is_pinned:
            return

        if not self.setting_legacy_pin_pos:
            return

        layout = _SHARED_LAYOUT_CACHE.get(cell_id)
        if layout is None:
            return

        try:
            pin_left, pin_top, icon_w, icon_h, pin_drawable = layout
            canvas.save()
            pin_drawable.setBounds(int(pin_left), int(pin_top), int(pin_left + icon_w), int(pin_top + icon_h))
            pin_drawable.draw(canvas)
            canvas.restore()
        except Exception as e:
            self.plugin.log(f"[after layout draw] {e}")
