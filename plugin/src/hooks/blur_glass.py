from base_plugin import MethodHook


def _flatten_drawable(drawable):
    """Force radius=0.1 and padding=0 on a BlurredBackgroundDrawable."""
    if drawable is None:
        return
    try:
        from java.lang import Float
        try:
            drawable.setRadius(Float(0.1))
        except Exception:
            try:
                drawable.setRadius(0.1)
            except Exception:
                pass
    except Exception:
        pass
    try:
        from java.lang import Integer
        drawable.setPadding(Integer(0))
    except Exception:
        try:
            drawable.setPadding(0)
        except Exception:
            pass


def _get_field(obj, field_name):
    try:
        cls = obj.getClass()
        while cls is not None:
            try:
                f = cls.getDeclaredField(field_name)
                f.setAccessible(True)
                return f.get(obj)
            except Exception:
                cls = cls.getSuperclass()
        return None
    except Exception:
        return None

def _set_field(obj, field_name, value):
    try:
        cls = obj.getClass()
        while cls is not None:
            try:
                f = cls.getDeclaredField(field_name)
                f.setAccessible(True)
                f.set(obj, value)
                return True
            except Exception:
                cls = cls.getSuperclass()
        return False
    except Exception:
        return False




class ChatInputBubbleHook(MethodHook):
    """After ChatInputViewsContainer.setInputIslandBubbleDrawable(), flatten the bubble drawable."""

    def __init__(self, plugin):
        self.plugin = plugin

    def after_hooked_method(self, param):
        if not self.plugin.get_setting("rectangular_ui", False):
            return
        try:
            drawable = param.args[0]
            _flatten_drawable(drawable)
            # Also flatten the stored reference (in case it differs)
            stored = _get_field(param.thisObject, "blurredBackgroundDrawable")
            if stored is not None:
                _flatten_drawable(stored)
        except Exception:
            pass


class ChatInputUnderKeyboardHook(MethodHook):
    """After ChatInputViewsContainer.setUnderKeyboardBackgroundDrawable(), flatten it too."""

    def __init__(self, plugin):
        self.plugin = plugin

    def after_hooked_method(self, param):
        if not self.plugin.get_setting("rectangular_ui", False):
            return
        try:
            drawable = param.args[0]
            _flatten_drawable(drawable)
        except Exception:
            pass


class ChatInputContainerPositionHook(MethodHook):
    """Force the chat input container blur to stretch horizontally."""

    def __init__(self, plugin):
        self.plugin = plugin

    def after_hooked_method(self, param):
        if not self.plugin.get_setting("rectangular_ui", False):
            return
        try:
            container = param.thisObject
            
            # Make blur stretch horizontally
            try:
                from java.lang import Float
                _set_field(container, "inputBubbleOffsetLeft", Float(0.0))
                _set_field(container, "inputBubbleOffsetRight", Float(0.0))
            except Exception:
                try:
                    _set_field(container, "inputBubbleOffsetLeft", 0.0)
                    _set_field(container, "inputBubbleOffsetRight", 0.0)
                except Exception:
                    pass
        except Exception:
            pass


class ChatInputDispatchDrawHook(MethodHook):
    """Stretch the chat input blur vertically to cover the navbar during draw."""

    def __init__(self, plugin):
        self.plugin = plugin
        
    def before_hooked_method(self, param):
        if not self.plugin.get_setting("rectangular_ui", False):
            return
        try:
            container = param.thisObject
            self.original_height = _get_field(container, "inputBubbleHeightRound")
            max_bottom = _get_field(container, "maxBottomInset")
            
            if self.original_height is not None and max_bottom is not None:
                from org.telegram.messenger import AndroidUtilities
                from java.lang import Integer
                
                # The gap below the input field (maxBottomInset + 9dp)
                gap = int(float(max_bottom)) + AndroidUtilities.dp(9.0)
                
                # Add gap to inputBubbleHeightRound so the blur stretches DOWN to the screen edge.
                # Do NOT modify currentBlurredHeight, so tmpRect.top stays locked to the text field!
                _set_field(container, "inputBubbleHeightRound", Integer(int(self.original_height) + gap))
        except Exception:
            pass
            
    def after_hooked_method(self, param):
        try:
            container = param.thisObject
            from java.lang import Integer
            if hasattr(self, "original_height") and self.original_height is not None:
                _set_field(container, "inputBubbleHeightRound", Integer(int(self.original_height)))
        except Exception:
            pass

class ChatActivityTopPanelBoundsHook(MethodHook):
    """Stretch the clipPath and backgroundDrawable bounds before dispatchDraw to fill gaps and suppress top divider."""

    def __init__(self, plugin):
        self.plugin = plugin
        self._saved_divider_alpha = None

    def before_hooked_method(self, param):
        if not self.plugin.get_setting("rectangular_ui", False):
            return
        try:
            layout = param.thisObject
            bg = _get_field(layout, "backgroundDrawable")
            
            try:
                from org.telegram.messenger import AndroidUtilities
                side_ext = AndroidUtilities.dp(7.0)
                top_ext = AndroidUtilities.dp(20.0)
            except Exception:
                side_ext = 0
                top_ext = 0

            if bg is not None:
                # Snapshot vertical bottom bound (recomputed freshly by checkBoundsAndClipping).
                raw = bg.getBounds()
                curr_bottom = int(raw.bottom)
                
                # 1. Extend bounds edge-to-edge horizontally and upwards under ActionBar to kill any gap.
                try:
                    bg.setBounds(-side_ext, -top_ext, int(layout.getMeasuredWidth()) + side_ext, curr_bottom)
                except Exception:
                    pass
                
                # 2. Zero radius via the PUBLIC setRadius() API.
                try:
                    bg.setRadius(0.0)
                except Exception:
                    try:
                        from java.lang import Float
                        bg.setRadius(Float(0.0))
                    except Exception:
                        pass
            
            # 3. Reset clipPath to a full rect (including top_ext) so children/background are never rounded-clipped.
            clipPath = _get_field(layout, "clipPath")
            if clipPath is not None:
                try:
                    from hook_utils import find_class
                    PathDirection = find_class("android.graphics.Path$Direction")
                    clipPath.rewind()
                    clipPath.addRect(
                        -float(side_ext), -float(top_ext),
                        float(layout.getMeasuredWidth()) + float(side_ext),
                        float(layout.getMeasuredHeight()),
                        PathDirection.CW
                    )
                except Exception:
                    pass

            # 4. Suppress the 1px forcedDividerPaint line drawn by dispatchDraw at y=0
            try:
                from hook_utils import find_class
                Theme = find_class("org.telegram.ui.ActionBar.Theme")
                paint = getattr(Theme, "forcedDividerPaint", None)
                if paint is not None:
                    self._saved_divider_alpha = int(paint.getAlpha())
                    paint.setAlpha(0)
            except Exception:
                self._saved_divider_alpha = None
        except Exception:
            pass

    def after_hooked_method(self, param):
        try:
            if self._saved_divider_alpha is not None:
                from hook_utils import find_class
                Theme = find_class("org.telegram.ui.ActionBar.Theme")
                paint = getattr(Theme, "forcedDividerPaint", None)
                if paint is not None:
                    paint.setAlpha(self._saved_divider_alpha)
        except Exception:
            pass


class TopPanelPaddingHook(MethodHook):
    """Force ChatActivityTopPanelLayout padding to 0 to stretch to edges."""
    def __init__(self, plugin):
        self.plugin = plugin
        
    def before_hooked_method(self, param):
        if not self.plugin.get_setting("rectangular_ui", False):
            return
        # Zero out ONLY paddingTop (index 1) to eliminate the gap between the
        # action bar and the pinned content. paddingBottom (index 3) is kept
        # so the panel height stays the same as vanilla.
        try:
            from java.lang import Integer
            param.args[1] = Integer(0)   # paddingTop → 0
        except Exception:
            pass




class ActionBarSetupGlassHook(MethodHook):
    """Replace 3 floating pills with a single contiguous blurred background."""
    def __init__(self, plugin):
        self.plugin = plugin
        
    def after_hooked_method(self, param):
        if not self.plugin.get_setting("rectangular_ui", False):
            return
        try:
            bar = param.thisObject
            factory = param.args[0]

            provider = param.args[1]
            
            # Create a single full-width BlurredBackgroundDrawable
            custom_blur = factory.create(bar)
            custom_blur.setColorProvider(provider)
            try:
                from java.lang import Float
                custom_blur.setRadius(Float(0.1))
            except Exception:
                try:
                    custom_blur.setRadius(0.1)
                except Exception:
                    pass
                    
            try:
                from java.lang import Integer
                custom_blur.setPadding(Integer(0))
            except Exception:
                try:
                    custom_blur.setPadding(0)
                except Exception:
                    pass
            
            # Replace background with our custom contiguous blur
            bar.setBackground(custom_blur)
            
            # Disable glassMode so it stops drawing the 3 floating pills
            try:
                from java.lang import Boolean
                _set_field(bar, "glassMode", Boolean(False))
            except Exception:
                _set_field(bar, "glassMode", False)

            # Disable shadow/divider drawn below ActionBar
            try:
                from java.lang import Float
                bar.setGlassShadowAlpha(Float(0.0))
                bar.setShadowAlpha(Float(0.0))
            except Exception:
                try:
                    bar.setGlassShadowAlpha(0.0)
                    bar.setShadowAlpha(0.0)
                except Exception:
                    pass
                
            # Clear out the old floating pills just in case
            _set_field(bar, "glassDrawable", None)
            _set_field(bar, "glassDrawableBack", None)
            _set_field(bar, "glassDrawableMenu", None)
            
        except Exception:
            pass

