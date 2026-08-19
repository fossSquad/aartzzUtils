from collections import OrderedDict
from time import time
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


class _SettingsCache:
    def __init__(self, plugin):
        self.plugin = plugin
        self._ts = 0.0
        self._values = {}

    def get(self, key, default=False):
        now = time()
        if now - self._ts > 1.0:
            self._ts = now
            self._values = {
                "legacy_pin_pos": self.plugin.get_setting("legacy_pin_pos", False),
                "pinned_bg": self.plugin.get_setting("pinned_bg", False),
                "hide_pin_if_unread": self.plugin.get_setting("hide_pin_if_unread", False),
            }
        return self._values.get(key, default)


_SHARED_LAYOUT_CACHE = _BoundedState(256)


class DialogCellBuildLayoutHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin
        self.fields = _FieldCache()
        self.settings = _SettingsCache(plugin)
        self.ThemeProxy = find_class("org.telegram.ui.ActionBar.Theme")
        self.AndroidUtilities = find_class("org.telegram.messenger.AndroidUtilities")
        self.LocaleController = find_class("org.telegram.messenger.LocaleController")
        # Original drawPin/drawPinForced values saved by the before-hook so the
        # after-hook still knows the cell is pinned after suppression.
        self._pinned_origins = _BoundedState(256)

    def before_hooked_method(self, param):
        # Suppress the default pin BEFORE buildLayout computes the layout so
        # the date/time stays anchored to the right edge. update() rewrites
        # these flags before buildLayout on every state change, so the
        # suppression persists without any per-frame reflection. The original
        # values are stashed per cell for the after-hook to read.
        if not self.settings.get("legacy_pin_pos", False):
            return
        this = param.thisObject
        try:
            dp = self.fields.get(this, "drawPin", False)
            dpf = self.fields.get(this, "drawPinForced", False)
            if dp or dpf:
                self._pinned_origins.set(_java_identity(this), (dp, dpf))
                self.fields.set(this, "drawPin", False)
                self.fields.set(this, "drawPinForced", False)
        except Exception:
            pass

    def after_hooked_method(self, param):
        legacy_pin = self.settings.get("legacy_pin_pos", False)
        pinned_bg = self.settings.get("pinned_bg", False)
        if not legacy_pin and not pinned_bg:
            return

        this = param.thisObject
        cell_id = _java_identity(this)
        try:
            orig = self._pinned_origins.pop(cell_id, None)
            if orig is not None:
                is_pinned = bool(orig[0]) or bool(orig[1])
            else:
                dp = self.fields.get(this, "drawPin", False)
                dpf = self.fields.get(this, "drawPinForced", False)
                is_pinned = bool(dp) or bool(dpf)
        except Exception:
            is_pinned = False

        if not is_pinned:
            _SHARED_LAYOUT_CACHE.pop(cell_id, None)
            return

        try:
            measured_w = int(this.getMeasuredWidth())
            measured_h = int(this.getMeasuredHeight())
        except Exception:
            measured_w = 0
            measured_h = 0

        if not legacy_pin:
            _SHARED_LAYOUT_CACHE.set(cell_id, (True, None, measured_w, measured_h))
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

            if self.settings.get("hide_pin_if_unread", False) and (unread_count != 0 or mark_unread):
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

            is_rtl = False
            try:
                if self.LocaleController is not None and hasattr(self.LocaleController, "isRTL"):
                    is_rtl = bool(self.LocaleController.isRTL)
            except Exception:
                pass

            icon_w = pin_drawable.getIntrinsicWidth()
            icon_h = pin_drawable.getIntrinsicHeight()
            measured_w = this.getMeasuredWidth()

            try:
                count_top = int(self.fields.get(this, "countTop"))
            except Exception:
                count_top = AndroidUtilities.dp(39.0)

            pin_top = count_top + (AndroidUtilities.dp(20.0) - icon_h) // 2

            badge_gap = AndroidUtilities.dp(6.0)

            if not is_rtl:
                if unread_count != 0 or mark_unread or draw_count:
                    try:
                        count_left = int(self.fields.get(this, "countLeft"))
                        pin_left = count_left - icon_w - badge_gap
                    except Exception:
                        pin_left = measured_w - icon_w - AndroidUtilities.dp(14.0)
                else:
                    pin_left = measured_w - icon_w - AndroidUtilities.dp(14.0)

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
            else:
                pin_left = AndroidUtilities.dp(14.0)
                if unread_count != 0 or mark_unread or draw_count:
                    try:
                        count_left = int(self.fields.get(this, "countLeft"))
                        count_w = int(self.fields.get(this, "countWidth", 0))
                        pin_left = max(pin_left, count_left + count_w + AndroidUtilities.dp(11.0) + badge_gap)
                    except Exception:
                        pass
                if bool(self.fields.get(this, "drawReactionMention", False)):
                    reaction_left = self.fields.get(this, "reactionMentionLeft")
                    if reaction_left is not None:
                        pin_left = max(pin_left, int(reaction_left) + AndroidUtilities.dp(25.0) + badge_gap)
                if bool(self.fields.get(this, "drawPollVotesMention", False)):
                    poll_left = self.fields.get(this, "pollVotesMentionLeft")
                    if poll_left is not None:
                        pin_left = max(pin_left, int(poll_left) + AndroidUtilities.dp(25.0) + badge_gap)
                if bool(self.fields.get(this, "drawMention", False)):
                    mention_left = self.fields.get(this, "mentionLeft")
                    mention_w = int(self.fields.get(this, "mentionWidth", 0))
                    if mention_left is not None:
                        pin_left = max(pin_left, int(mention_left) + mention_w + AndroidUtilities.dp(11.0) + badge_gap)
                if bool(self.fields.get(this, "drawError", False)):
                    error_left = self.fields.get(this, "errorLeft")
                    if error_left is not None:
                        pin_left = max(pin_left, int(error_left) + AndroidUtilities.dp(29.0) + badge_gap)

            _SHARED_LAYOUT_CACHE.set(
                cell_id, (True, (int(pin_left), int(pin_top), int(icon_w), int(icon_h), pin_drawable), measured_w, measured_h)
            )
            # No log here: it flooded logcat and evicted other diagnostics.
        except Exception as e:
            self.plugin.log(f"[buildLayout after] {e}")


class DialogCellOnDrawHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin
        self.fields = _FieldCache()
        self.settings = _SettingsCache(plugin)
        self.ThemeProxy = find_class("org.telegram.ui.ActionBar.Theme")
        self.key_chats_pinnedOverlay = getattr(self.ThemeProxy, "key_chats_pinnedOverlay", None)
        self.bg_paint = None
        self._color_ts = 0.0
        self._color = None
        self._logged = set()

    def _overlay_color(self, this):
        now = time()
        if now - self._color_ts > 2.0 or self._color is None:
            self._color_ts = now
            color = None
            if self.key_chats_pinnedOverlay is not None:
                try:
                    rp = self.fields.get(this, "resourcesProvider")
                    color = self.ThemeProxy.getColor(self.key_chats_pinnedOverlay, rp)
                except Exception:
                    try:
                        color = self.ThemeProxy.getColor(self.key_chats_pinnedOverlay)
                    except Exception:
                        color = None
            self._color = color
        return self._color

    def before_hooked_method(self, param):
        if not self.settings.get("pinned_bg", False):
            return
        this = param.thisObject
        try:
            entry = _SHARED_LAYOUT_CACHE.get(_java_identity(this))
            if entry is None or not entry[0]:
                return
            canvas = param.args[0]
            if self.bg_paint is None:
                from android.graphics import Paint
                self.bg_paint = Paint()
            color = self._overlay_color(this)
            if color is not None:
                self.bg_paint.setColor(color)
                self.bg_paint.setAlpha(15)
                w = entry[2] or this.getMeasuredWidth()
                h = entry[3] or this.getMeasuredHeight()
                canvas.drawRect(0.0, 0.0, float(w), float(h), self.bg_paint)
        except Exception:
            pass

    def after_hooked_method(self, param):
        if not self.settings.get("legacy_pin_pos", False):
            return
        this = param.thisObject
        canvas = param.args[0]
        try:
            cell_id = _java_identity(this)
            entry = _SHARED_LAYOUT_CACHE.get(cell_id)
            if entry is None:
                return
            is_pinned, layout, _, _ = entry
            if not is_pinned or layout is None:
                return
            pin_left, pin_top, icon_w, icon_h, pin_drawable = layout
            pin_drawable.setBounds(pin_left, pin_top, pin_left + icon_w, pin_top + icon_h)
            pin_drawable.draw(canvas)
            if cell_id not in self._logged:
                self._logged.add(cell_id)
                self.plugin.log(f"[pinned] drawn id={cell_id} pos=({pin_left},{pin_top})")
        except Exception as e:
            self.plugin.log(f"[after layout draw] {e}")