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
        try:
            drawable = param.args[0]
            _flatten_drawable(drawable)
        except Exception:
            pass


class ChatInputContainerPositionHook(MethodHook):
    """Override checkViewsPositions to remove the 9dp floating gap.

    Original: inputIslandBubbleContainer.setTranslationY(-maxBottomInset - dp(9))
    We want:  inputIslandBubbleContainer.setTranslationY(-maxBottomInset)
    This makes the input bar sit flush at the bottom instead of floating.
    """

    def __init__(self, plugin):
        self.plugin = plugin

    def after_hooked_method(self, param):
        try:
            container = param.thisObject
            island = _get_field(container, "inputIslandBubbleContainer")
            if island is None:
                return
            max_bottom_inset = _get_field(container, "maxBottomInset")
            if max_bottom_inset is None:
                max_bottom_inset = 0.0
            island.setTranslationY(-float(max_bottom_inset))
        except Exception:
            pass


class ChatInputContainerHeightHook(MethodHook):
    """Decrease the blurred background height by 9dp to match the flush views position."""

    def __init__(self, plugin):
        self.plugin = plugin

    def before_hooked_method(self, param):
        try:
            from org.telegram.messenger import AndroidUtilities
            from java.lang import Float
            
            if param.method.getName() == "setBlurredBottomHeight":
                val = param.args[0]
                param.args[0] = Float(float(val) - AndroidUtilities.dp(9.0))
        except Exception:
            pass
            
    def after_hooked_method(self, param):
        try:
            if param.method.getName() == "checkBlurredHeight":
                from org.telegram.messenger import AndroidUtilities
                container = param.thisObject
                current_height = _get_field(container, "currentBlurredHeight")
                if current_height is not None:
                    _set_field(container, "currentBlurredHeight", int(current_height) - AndroidUtilities.dp(9.0))
        except Exception:
            pass




class ChatActivityTopPanelBoundsHook(MethodHook):
    """Flatten the clipPath and backgroundDrawable radius before dispatchDraw."""

    def __init__(self, plugin):
        self.plugin = plugin

    def before_hooked_method(self, param):
        try:
            layout = param.thisObject
            
            # Flatten clipPath
            clipPath = _get_field(layout, "clipPath")
            clipRectF = _get_field(layout, "clipRectF")
            if clipPath is not None and clipRectF is not None:
                from android.graphics import Path
                clipPath.rewind()
                clipPath.addRect(clipRectF, Path.Direction.CW)
            
            # Flatten background blur radius
            bg = _get_field(layout, "backgroundDrawable")
            if bg is not None:
                try:
                    from java.lang import Float
                    bg.setRadius(Float(0.1))
                except Exception:
                    try:
                        bg.setRadius(0.1)
                    except Exception:
                        pass
        except Exception:
            pass



class ActionBarSetupGlassHook(MethodHook):
    """Replace 3 floating pills with a single contiguous blurred background."""
    def __init__(self, plugin):
        self.plugin = plugin
        
    def after_hooked_method(self, param):
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

                
            # Clear out the old floating pills just in case
            _set_field(bar, "glassDrawable", None)
            _set_field(bar, "glassDrawableBack", None)
            _set_field(bar, "glassDrawableMenu", None)
            
        except Exception:
            pass

