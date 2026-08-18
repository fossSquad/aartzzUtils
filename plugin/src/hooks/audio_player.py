from base_plugin import MethodHook
from android_utils import OnLongClickListener


class AudioPlayerTopBarHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin

    def after_hooked_method(self, param):
        if not self.plugin.get_setting("audio_bar_long_click", False):
            return

        try:
            view = param.thisObject

            def handle_long_click(v):
                try:
                    if not self.plugin.get_setting("audio_bar_long_click", False):
                        return False

                    current_style = getattr(v, "currentStyle", -1)
                    if current_style != 0:
                        return False

                    from org.telegram.messenger import MediaController, DialogObject
                    from org.telegram.ui import ChatActivity
                    from android.os import Bundle

                    message_object = MediaController.getInstance().getPlayingMessageObject()
                    if message_object is None:
                        return False

                    fragment = getattr(v, "fragment", None)
                    if fragment is None:
                        return False

                    chat_activity = getattr(v, "chatActivity", None)
                    dialog_id = 0
                    if chat_activity is not None:
                        dialog_id = chat_activity.getDialogId()

                    msg_dialog_id = message_object.getDialogId()
                    if msg_dialog_id == dialog_id and chat_activity is not None:
                        chat_activity.scrollToMessageId(message_object.getId(), 0, False, 0, True, 0)
                        return True
                    else:
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
                except Exception:
                    return False

            view.setOnLongClickListener(OnLongClickListener(handle_long_click))
        except Exception:
            pass

