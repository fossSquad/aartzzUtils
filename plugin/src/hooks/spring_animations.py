from base_plugin import MethodHook
from hook_utils import get_private_field

class SpringAnimationsHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin

    def before_hooked_method(self, param):
        if self.plugin.get_setting("disable_spring_shrink", False):
            try:
                this = param.thisObject
                cv = get_private_field(this, "containerView")
                if cv is not None:
                    cv.setScaleX(1.0)
                    cv.setScaleY(1.0)
                cvb = get_private_field(this, "containerViewBack")
                if cvb is not None:
                    cvb.setScaleX(1.0)
                    cvb.setScaleY(1.0)
            except Exception:
                pass

class VoiceVideoAnimHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin
        
    def after_hooked_method(self, param):
        if not self.plugin.get_setting("voice_video_anim", False):
            return
            
        try:
            buttonsAnimation = get_private_field(param.thisObject, "buttonsAnimation")
            if buttonsAnimation:
                from java.lang import Class as JavaClass
                OvershootInterpolatorClass = JavaClass.forName("android.view.animation.OvershootInterpolator")
                if OvershootInterpolatorClass:
                    interpolator = OvershootInterpolatorClass.getConstructor([]).newInstance([])
                    buttonsAnimation.setInterpolator(interpolator)
                    buttonsAnimation.setDuration(300)
        except Exception:
            pass
