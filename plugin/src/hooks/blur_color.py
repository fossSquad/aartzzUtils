from collections import OrderedDict

from base_plugin import MethodHook


def _java_identity(instance):
    return hash(instance)


def _dim_color(color, dim_amount):
    value = int(color) & 0xFFFFFFFF
    dim_amount = max(0.0, min(1.0, float(dim_amount)))
    factor = 1.0 - dim_amount
    alpha = value & 0xFF000000
    red = int(((value >> 16) & 0xFF) * factor)
    green = int(((value >> 8) & 0xFF) * factor)
    blue = int((value & 0xFF) * factor)
    result = alpha | (red << 16) | (green << 8) | blue
    return result if result < 0x80000000 else result - 0x100000000


class WallpaperSourceDimHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin
        self.dim_by_provider = OrderedDict()

    def after_hooked_method(self, param):
        if not self.plugin.get_setting("blur_dim_wallpaper", True):
            return

        try:
            drawable = param.args[0]
            dim_amount = 0.0
            if drawable is not None and "ChatBackgroundDrawable" in drawable.getClass().getName():
                dim_amount = float(drawable.getDimAmount())
            provider_id = _java_identity(param.thisObject)
            self.dim_by_provider[provider_id] = dim_amount
            self.dim_by_provider.move_to_end(provider_id)
            while len(self.dim_by_provider) > 32:
                self.dim_by_provider.popitem(last=False)
        except Exception:
            self.dim_by_provider[_java_identity(param.thisObject)] = 0.0


class WallpaperColorDimHook(MethodHook):
    def __init__(self, plugin, source_hook):
        self.plugin = plugin
        self.source_hook = source_hook

    def after_hooked_method(self, param):
        if not self.plugin.get_setting("blur_dim_wallpaper", True):
            return

        try:
            dim_amount = self.source_hook.dim_by_provider.get(
                _java_identity(param.thisObject), 0.0
            )
            if dim_amount > 0.0:
                param.setResult(_dim_color(param.getResult(), dim_amount))
        except Exception:
            pass
