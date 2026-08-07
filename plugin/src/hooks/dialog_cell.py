from base_plugin import MethodHook
from hook_utils import find_class, get_private_field

class DialogCellBuildLayoutHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin
        self.alpha_hidden_map = {}

    def before_hooked_method(self, param):
        this = param.thisObject
        cell_id = this.hashCode()
        alpha_hidden = False
        
        try:
            dp = get_private_field(this, "drawPin")
            dpf = False
            try:
                dpf = get_private_field(this, "drawPinForced")
            except Exception:
                pass
            
            is_pinned = bool(dp) or bool(dpf)
            
            if is_pinned and self.plugin.get_setting("legacy_pin_pos", True):
                from hook_utils import set_private_field
                set_private_field(this, "drawPin", False)
                set_private_field(this, "drawPinForced", False)
                alpha_hidden = True
        except Exception:
            pass
        finally:
            self.alpha_hidden_map[cell_id] = alpha_hidden

    def after_hooked_method(self, param):
        this = param.thisObject
        cell_id = this.hashCode()
        alpha_hidden = self.alpha_hidden_map.pop(cell_id, False)

        if alpha_hidden:
            try:
                from hook_utils import set_private_field
                set_private_field(this, "drawPin", True)
            except Exception:
                pass

class DialogCellOnDrawHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin
        self.state_map = {}

    def before_hooked_method(self, param):
        this = param.thisObject
        cell_id = this.hashCode()
        alpha_hidden = False
        is_pinned = False
        
        try:
            # We must set is_pinned based on drawPin or drawPinForced
            dp = get_private_field(this, "drawPin")
            dpf = False
            try:
                dpf = get_private_field(this, "drawPinForced")
            except Exception:
                pass
            
            is_pinned = bool(dp) or bool(dpf)

            ThemeProxy = find_class("org.telegram.ui.ActionBar.Theme")
            
            # Draw legacy pinned highlight
            if is_pinned and self.plugin.get_setting("pinned_chat_highlight", True):
                canvas = param.args[0]
                if not hasattr(self, "bg_paint"):
                    from android.graphics import Paint
                    self.bg_paint = Paint()
                try:
                    try:
                        rp = get_private_field(this, "resourcesProvider")
                        color = ThemeProxy.getColor(ThemeProxy.key_chats_pinnedOverlay, rp)
                    except Exception:
                        color = ThemeProxy.getColor(ThemeProxy.key_chats_pinnedOverlay)
                    
                    self.bg_paint.setColor(color)
                    # Force the paint to be translucent so it doesn't paint solid white
                    self.bg_paint.setAlpha(15)
                    canvas.drawRect(0.0, 0.0, float(this.getMeasuredWidth()), float(this.getMeasuredHeight()), self.bg_paint)
                except Exception as e:
                    self.plugin.log(f"Highlight error: {e}")

            # Hide native pin icon by setting drawPin to False temporarily
            if is_pinned and self.plugin.get_setting("legacy_pin_pos", True):
                try:
                    from hook_utils import set_private_field
                    set_private_field(this, "drawPin", False)
                    set_private_field(this, "drawPinForced", False)
                    alpha_hidden = True # reusing this flag name for simplicity
                except Exception as e:
                    self.plugin.log(f"drawPin hide error: {e}")

        except Exception as e:
            self.plugin.log(f"[before] {e}")
        finally:
            self.state_map[cell_id] = {'pinned': is_pinned, 'alpha_hidden': alpha_hidden}

    def after_hooked_method(self, param):
        this = param.thisObject
        canvas = param.args[0]
        cell_id = this.hashCode()
        state = self.state_map.pop(cell_id, {'pinned': False, 'alpha_hidden': False})

        # ALWAYS restore drawPin first!
        if state['alpha_hidden']:
            try:
                from hook_utils import set_private_field
                set_private_field(this, "drawPin", True)
            except Exception:
                pass

        if not state['pinned']:
            return

        # Draw custom pin at bottom right
        if not self.plugin.get_setting("legacy_pin_pos", True):
            return

        try:
            ThemeProxy = find_class("org.telegram.ui.ActionBar.Theme")
            AndroidUtilities = find_class("org.telegram.messenger.AndroidUtilities")

            unread_count = 0
            mark_unread = False
            try:
                unread_count = int(get_private_field(this, "unreadCount"))
            except Exception:
                pass
            try:
                mark_unread = bool(get_private_field(this, "markUnread"))
            except Exception:
                pass

            if self.plugin.get_setting("hide_pin_if_unread", False) and (unread_count != 0 or mark_unread):
                return

            draw_count = False
            is_muted = False
            try:
                draw_count = bool(get_private_field(this, "drawCount"))
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
                return

            icon_w = pin_drawable.getIntrinsicWidth()
            icon_h = pin_drawable.getIntrinsicHeight()
            measured_w = this.getMeasuredWidth()

            try:
                count_top = int(get_private_field(this, "countTop"))
            except Exception:
                count_top = AndroidUtilities.dp(39.0)

            pin_top = count_top + (AndroidUtilities.dp(20.0) - icon_h) // 2

            if unread_count != 0 or mark_unread:
                try:
                    count_left = int(get_private_field(this, "countLeft"))
                    pin_left = count_left - icon_w - AndroidUtilities.dp(6.0)
                except Exception:
                    pin_left = measured_w - icon_w - AndroidUtilities.dp(14.0)
            else:
                pin_left = measured_w - icon_w - AndroidUtilities.dp(14.0)
            
            # Determine dynamic pin_left position (avoiding unread badge)
            pin_left = measured_w - icon_w - AndroidUtilities.dp(14.0)
            try:
                count_width = get_private_field(this, "countWidth")
                if count_width:
                    pin_left = measured_w - count_width - icon_w - AndroidUtilities.dp(24.0)
            except Exception:
                pass

            canvas.save()
            
            # Use gradient to perfectly fade out text into the background
            try:
                from android.graphics import Paint, LinearGradient
                TileMode = find_class("android.graphics.Shader$TileMode")
                
                def make_color(a, r, g, b):
                    val = (a << 24) | (r << 16) | (g << 8) | b
                    if val > 0x7FFFFFFF:
                        val -= 0x100000000
                    return val
                
                # Retrieve actual background colors to blend perfectly
                rp = None
                try:
                    rp = get_private_field(this, "resourcesProvider")
                except Exception:
                    pass
                
                if rp:
                    bg_color = ThemeProxy.getColor(ThemeProxy.key_windowBackgroundWhite, rp)
                    overlay_color = ThemeProxy.getColor(ThemeProxy.key_chats_pinnedOverlay, rp)
                else:
                    bg_color = ThemeProxy.getColor(ThemeProxy.key_windowBackgroundWhite)
                    overlay_color = ThemeProxy.getColor(ThemeProxy.key_chats_pinnedOverlay)
                    
                final_bg = bg_color
                r = (bg_color >> 16) & 0xff
                g = (bg_color >> 8) & 0xff
                b = bg_color & 0xff
                
                if self.plugin.get_setting("pinned_chat_highlight", True):
                    # Blend bg_color and overlay_color natively at 15% opacity to match our custom highlight
                    ratio = 15.0 / 255.0
                    r = int(((bg_color >> 16) & 0xff) * (1 - ratio) + ((overlay_color >> 16) & 0xff) * ratio)
                    g = int(((bg_color >> 8) & 0xff) * (1 - ratio) + ((overlay_color >> 8) & 0xff) * ratio)
                    b = int((bg_color & 0xff) * (1 - ratio) + (overlay_color & 0xff) * ratio)
                    
                final_bg = make_color(255, r, g, b)
                transparent_bg = make_color(0, r, g, b)
                
                pad = AndroidUtilities.dp(4.0)
                fade_w = AndroidUtilities.dp(24.0)
                
                bg_paint = Paint()
                gradient = LinearGradient(
                    float(pin_left - fade_w), 0.0,
                    float(pin_left), 0.0,
                    transparent_bg, final_bg,
                    TileMode.CLAMP
                )
                bg_paint.setShader(gradient)
                
                # Draw the fade gradient
                canvas.drawRect(float(pin_left - fade_w), float(pin_top - pad), float(pin_left), float(pin_top + icon_h + pad), bg_paint)
                
                # Draw solid background behind the pin
                solid_paint = Paint()
                solid_paint.setColor(final_bg)
                canvas.drawRect(float(pin_left), float(pin_top - pad), float(measured_w), float(pin_top + icon_h + pad), solid_paint)
            except Exception as e:
                self.plugin.log(f"Gradient error: {e}")

            pin_drawable.setBounds(int(pin_left), int(pin_top), int(pin_left + icon_w), int(pin_top + icon_h))
            pin_drawable.draw(canvas)
            canvas.restore()

        except Exception as e:
            self.plugin.log(f"[after] {e}")
