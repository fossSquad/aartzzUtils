from base_plugin import MethodHook
from android_utils import OnLongClickListener


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


class AudioPlayerTopBarHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin
        self.fields = _FieldCache()

    def after_hooked_method(self, param):
        if not self.plugin.get_setting("audio_bar_long_click", False):
            return

        try:
            view = param.thisObject

            def handle_long_click(v):
                try:
                    self.plugin.log("[audio bar] long click fired")
                    if not self.plugin.get_setting("audio_bar_long_click", False):
                        return False

                    # FragmentContextView fields are private and declared on the
                    # superclass (this is an anonymous subclass like ChatActivity$N),
                    # so walk the class hierarchy to find them.
                    # NOTE: no currentStyle check here — the app bails when the bar
                    # style is 0, but a visible playing bar can still report 0, so
                    # we rely on the getPlayingMessageObject() check below instead.

                    from org.telegram.messenger import MediaController, DialogObject
                    from org.telegram.ui import ChatActivity
                    from android.os import Bundle

                    message_object = MediaController.getInstance().getPlayingMessageObject()
                    if message_object is None:
                        self.plugin.log("[audio bar] no playing message")
                        return False

                    fragment = self.fields.get(view, "fragment")
                    if fragment is None:
                        self.plugin.log("[audio bar] fragment is None")
                        return False

                    # Always navigate to the message/chat ("Show in chat") —
                    # do NOT open the AudioPlayerAlert popup even for music,
                    # per user request.
                    chat_activity = self.fields.get(view, "chatActivity")
                    dialog_id = 0
                    if chat_activity is not None:
                        dialog_id = chat_activity.getDialogId()

                    msg_dialog_id = message_object.getDialogId()
                    if msg_dialog_id == dialog_id and chat_activity is not None:
                        self.plugin.log(f"[audio bar] scrolling to message {message_object.getId()}")
                        chat_activity.scrollToMessageId(message_object.getId(), 0, False, 0, True, 0)
                        return True

                    self.plugin.log(f"[audio bar] opening chat for dialog {msg_dialog_id}")
                    args = Bundle()
                    if DialogObject.isEncryptedDialog(msg_dialog_id):
                        args.putInt("enc_id", DialogObject.getEncryptedChatId(msg_dialog_id))
                    elif DialogObject.isUserDialog(msg_dialog_id):
                        args.putLong("user_id", msg_dialog_id)
                    else:
                        args.putLong("chat_id", -msg_dialog_id)
                    args.putInt("message_id", message_object.getId())

                    is_chat = isinstance(fragment, ChatActivity)
                    fragment.presentFragment(ChatActivity(args), is_chat)
                    return True
                except Exception as e:
                    self.plugin.log(f"[audio bar] handler error: {e}")
                    return False

            # Attach to the FragmentContextView itself. The app sets its own
            # long-click listener inside checkCreateView; our after-hook runs
            # after it, so ours wins. Children (selector/frameLayout) are
            # skipped because the parent consumes the touch first.
            view.setOnLongClickListener(OnLongClickListener(handle_long_click))
            self.plugin.log(f"[audio bar] listener attached to {view.getClass().getName()}")
        except Exception:
            pass