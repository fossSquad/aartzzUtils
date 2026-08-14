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
            Switch(
                key="hide_send_button_bg",
                text=strings("hide_send_button_bg_title"),
                subtext=strings("hide_send_button_bg_desc"),
                default=True,
                icon="msg_voice",
                on_change=lambda v: self.set_setting("hide_send_button_bg", v)
            ),
            Switch(
                key="legacy_outline_icons",
                text=strings("legacy_outline_icons_title"),
                subtext=strings("legacy_outline_icons_desc"),
                default=True,
                icon="msg_settings",
                on_change=lambda v: self.set_setting("legacy_outline_icons", v)
            ),
            Switch(
                key="disable_spring_shrink",
                text=strings("disable_spring_shrink_title"),
                subtext=strings("disable_spring_shrink_desc"),
                default=True,
                icon="msg_edit",
                on_change=lambda v: self.set_setting("disable_spring_shrink", v)
            ),
            Switch(
                key="hide_profile_levels",
                text=strings("hide_profile_levels_title"),
                subtext=strings("hide_profile_levels_desc"),
                default=True,
                icon="msg_user",
                on_change=lambda v: self.set_setting("hide_profile_levels", v)
            ),
            Switch(
                key="compose_pencil",
                text=strings("compose_pencil_title"),
                subtext=strings("compose_pencil_desc"),
                default=True,
                icon="msg_edit",
                on_change=lambda v: self.set_setting("compose_pencil", v)
            ),
            Switch(
                key="rectangular_ui",
                text=strings("rectangular_ui_title"),
                subtext=strings("rectangular_ui_desc"),
                default=True,
                icon="msg_edit",
                on_change=lambda v: self.set_setting("rectangular_ui", v)
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
            ] if self.get_setting("legacy_pin_pos", True) else []) + [
                Switch(
                    key="sidebar_contrast",
                    text=strings("sidebar_contrast_title"),
                    subtext=strings("sidebar_contrast_desc"),
                    default=True,
                    icon="msg_channel",
                    on_change=lambda v: self.set_setting("sidebar_contrast", v)
                ),
                Switch(
                    key="settings_account_info",
                    text=strings("settings_account_info_title"),
                    subtext=strings("settings_account_info_desc"),
                    default=True,
                    icon="msg_user",
                    on_change=lambda v: self.set_setting("settings_account_info", v)
                ),
                Switch(
                    key="legacy_settings_icons",
                    text=strings("legacy_settings_icons_title"),
                    subtext=strings("legacy_settings_icons_desc"),
                    default=True,
                    icon="msg_settings",
                 on_change=lambda v: self.set_setting("legacy_settings_icons", v)
                ),
                Switch(
                    key="camera_tile_single_cell",
                    text=strings("camera_tile_single_cell_title"),
                    subtext=strings("camera_tile_single_cell_desc"),
                    default=True,
                    icon="msg_camera",
                    on_change=lambda v: self.set_setting("camera_tile_single_cell", v)
                ),
                Switch(
                    key="blur_dim_wallpaper",
                    text=strings("blur_dim_wallpaper_title"),
                    subtext=strings("blur_dim_wallpaper_desc"),
                    default=True,
                    icon="msg_channel",
                    on_change=lambda v: self.set_setting("blur_dim_wallpaper", v)
                )]
