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
    """Force the chat input container blur to stretch horizontally."""

    def __init__(self, plugin):
        self.plugin = plugin

    def after_hooked_method(self, param):
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
    """Stretch the clipPath and backgroundDrawable bounds before dispatchDraw to fill gaps."""

    def __init__(self, plugin):
        self.plugin = plugin

    def after_hooked_method(self, param):
        try:
            layout = param.thisObject
            bg = _get_field(layout, "backgroundDrawable")
            
            if bg is not None:
                bounds = bg.getBounds()
                
                try:
                    trans_y = float(layout.getTranslationY())
                    top_bound = int(-trans_y)
                    if top_bound > 0:
                        top_bound = 0
                        
                    try:
                        from org.telegram.messenger import AndroidUtilities
                        padding = AndroidUtilities.dp(8.0)
                    except Exception:
                        padding = 0
                        
                    bg.setBounds(-padding, top_bound - padding, int(layout.getMeasuredWidth()) + padding, int(bounds.bottom) + padding)
                except Exception:
                    pass
                
                try:
                    for i in range(8):
                        bg.boundProps.radii[i] = 0.0
                        bg.boundProps.shaderRadii[i] = 0.0
                    bg.boundProps.build()
                except Exception as e:
                    pass
                        
            clipPath = _get_field(layout, "clipPath")
            if clipPath is not None and bg is not None:
                try:
                    from android.graphics import Path
                    bounds = bg.getBounds()
                    clipPath.rewind()
                    clipPath.addRect(0.0, float(bounds.top), float(bounds.right), float(bounds.bottom), Path.Direction.CW)
                except Exception:
                    pass
        except Exception:
            pass

class TopPanelPaddingHook(MethodHook):
    """Force ChatActivityTopPanelLayout padding to 0 to stretch to edges."""
    def __init__(self, plugin):
        self.plugin = plugin
        
    def before_hooked_method(self, param):
        try:
            from java.lang import Integer
            param.args[0] = Integer(0)
            param.args[1] = Integer(0)
            param.args[2] = Integer(0)
            param.args[3] = Integer(0)
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

