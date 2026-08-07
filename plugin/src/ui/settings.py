from typing import List, Any
from ui.settings import Header, Switch
from elyx import strings

class SettingsMixin:
    def create_settings(self) -> List[Any]:
        return [
            Header(text=strings("settings_chat_header")),
            Switch(
                key="voice_video_anim",
                text=strings("voice_video_anim_title"),
                subtext=strings("voice_video_anim_desc"),
                default=True,
                icon="msg_voice",
                on_change=lambda v: self.set_setting("voice_video_anim", v)
            ),
            Header(text=strings("settings_home_header")),
            Switch(
                key="pinned_bg",
                text=strings("pinned_bg_title"),
                subtext=strings("pinned_bg_desc"),
                default=True,
                icon="msg_channel",
                on_change=lambda v: self.set_setting("pinned_bg", v)
            ),
            Switch(
                key="legacy_pin_pos",
                text=strings("legacy_pin_pos_title"),
                subtext=strings("legacy_pin_pos_desc"),
                default=True,
                icon="msg_pin",
                on_change=lambda v: self.set_setting("legacy_pin_pos", v, reload_settings=True)
            )] + ([
                Switch(
                    key="hide_pin_if_unread",
                    text=strings("hide_pin_if_unread_title"),
                    subtext=strings("hide_pin_if_unread_desc"),
                    default=False,
                    icon="msg_archive",
                    on_change=lambda v: self.set_setting("hide_pin_if_unread", v)
                )
            ] if self.get_setting("legacy_pin_pos", True) else [])
