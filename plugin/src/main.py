from elyx import strings
from base_plugin import BasePlugin
from java.lang import Class as JavaClass

from .hooks import (
    IsBasePackOnlyHook,
    DialogCellOnDrawHook,
    DialogCellBuildLayoutHook,
    GetThemedColorHook,
    SendButtonOnDrawHook,
    SendButtonUpdateColorsHook,
    AudioVideoOutlineHook,
    SpringAnimationsHook,
    VoiceVideoAnimHook,
    ProfileLevelsHook,
    ImmersiveDrawerHook,
    SettingsAccountInfoHook,
    SettingsAccountOnClickHook,
    SettingsAccountOnLongClickHook,
    ComposeButtonHook,
    SettingsIconsHook,
    AudioPlayerTopBarHook,
    CameraTileSingleCellHook,

    ChatInputBubbleHook,
    ChatInputUnderKeyboardHook,
    ChatInputContainerPositionHook,
    ChatInputDispatchDrawHook,
    ChatActivityTopPanelBoundsHook,
    ActionBarSetupGlassHook,
    TopPanelPaddingHook,
)
from .ui import SettingsMixin

class ExteraRestorePlugin(SettingsMixin, BasePlugin):
    def on_plugin_load(self):
        self.log(strings("loaded"))

        # 1. Hook IconManager
        IconManagerClass = JavaClass.forName("com.exteragram.messenger.icons.IconManager")
        IconPackTypeClass = JavaClass.forName("com.exteragram.messenger.IconPackType")
        if IconManagerClass and IconPackTypeClass:
            try:
                is_base_pack_only_method = IconManagerClass.getDeclaredMethod("isBasePackOnly", IconPackTypeClass)
                is_base_pack_only_method.setAccessible(True)
                self.hook_method(is_base_pack_only_method, IsBasePackOnlyHook(self))
                self.log("Hooked IconManager.isBasePackOnly")
            except Exception as e:
                self.log(f"Failed to hook IconManager: {e}")

        # 2. Hook DialogCell.onDraw
        DialogCellClass = JavaClass.forName("org.telegram.ui.Cells.DialogCell")
        if DialogCellClass:
            # Hook buildLayout to fix date spacing
            self.hook_all_methods(DialogCellClass, "buildLayout", DialogCellBuildLayoutHook(self))
            
            # Hook onDraw to handle drawing legacy highlight and pin
            hooked = self.hook_all_methods(DialogCellClass, "onDraw", DialogCellOnDrawHook(self))
            if hooked:
                self.log("Hooked DialogCell.onDraw")
            else:
                self.log("Failed to hook DialogCell.onDraw")

        # 3. Hook ChatActivityEnterView (Voice/Video button background)
        ChatActivityEnterViewClass = JavaClass.forName("org.telegram.ui.Components.ChatActivityEnterView")
        if ChatActivityEnterViewClass:
            hooked = self.hook_all_methods(ChatActivityEnterViewClass, "getThemedColor", GetThemedColorHook(self))
            if hooked:
                self.log("Hooked ChatActivityEnterView.getThemedColor")
            else:
                self.log("Failed to hook ChatActivityEnterView.getThemedColor")

        # 4. Hook SendButton (Typing mode send button background)
        SendButtonClass = JavaClass.forName("org.telegram.ui.Components.ChatActivityEnterView$SendButton")
        if SendButtonClass:
            hooked = self.hook_all_methods(SendButtonClass, "onDraw", SendButtonOnDrawHook(self))
            if hooked:
                self.log("Hooked SendButton.onDraw")
            else:
                self.log("Failed to hook SendButton.onDraw")
            # SendButton.updateColors() sets backgroundPaint directly from Theme
            # at the start of every onDraw (bypassing the outer getThemedColor),
            # so neutralize the paint here instead.
            hooked = self.hook_all_methods(SendButtonClass, "updateColors", SendButtonUpdateColorsHook(self))
            if hooked:
                self.log("Hooked SendButton.updateColors")
            else:
                self.log("Failed to hook SendButton.updateColors")

        # 4b. The voice/video (mic/camera) button is NOT ChatActivityEnterView$SendButton
        # (that is the text-send arrow). It lives in audioVideoSendButton as an anonymous
        # view: $25 (base icon pack) or $26 (legacy outline icons). Both override
        # draw(Canvas) and paint the circular outline first via outer.micOutline /
        # outer.cameraOutline, then super.draw() renders the glyph.
        for audio_video_name in (
            "org.telegram.ui.Components.ChatActivityEnterView$25",
            "org.telegram.ui.Components.ChatActivityEnterView$26",
        ):
            AudioVideoViewClass = JavaClass.forName(audio_video_name)
            if AudioVideoViewClass:
                hooked = self.hook_all_methods(AudioVideoViewClass, "draw", AudioVideoOutlineHook(self))
                if hooked:
                    self.log(f"Hooked {audio_video_name}.draw")
                else:
                    self.log(f"Failed to hook {audio_video_name}.draw")

        ActionBarLayoutClass = JavaClass.forName("org.telegram.ui.ActionBar.ActionBarLayout")
        if ActionBarLayoutClass:
            hooked = self.hook_all_methods(
                ActionBarLayoutClass, "dispatchDraw", SpringAnimationsHook(self)
            )
            if hooked:
                self.log("Hooked ActionBarLayout.dispatchDraw")
                
        ChatActivityEnterViewStaticIconViewClass = JavaClass.forName("com.exteragram.messenger.components.ChatActivityEnterViewStaticIconView")
        if ChatActivityEnterViewStaticIconViewClass:
            hooked = self.hook_all_methods(
                ChatActivityEnterViewStaticIconViewClass, "setState", VoiceVideoAnimHook(self)
            )
            if hooked:
                self.log("Hooked ChatActivityEnterViewStaticIconView.setState")


        ProfileActivityClass = JavaClass.forName("org.telegram.ui.ProfileActivity")
        if ProfileActivityClass:
            hooked = self.hook_all_methods(ProfileActivityClass, "createView", ProfileLevelsHook(self))
            if hooked:
                self.log("Hooked ProfileActivity.createView")

        DrawerContainerClass = JavaClass.forName("com.exteragram.messenger.drawer.DrawerContainer")
        if DrawerContainerClass:
            hooked = self.hook_all_methods(
                DrawerContainerClass, "getImmersiveDrawerAnimation", ImmersiveDrawerHook(self)
            )
            if hooked:
                self.log("Hooked DrawerContainer.getImmersiveDrawerAnimation")

        SettingsActivityClass = JavaClass.forName("org.telegram.ui.SettingsActivity")
        if SettingsActivityClass:
            hooked = self.hook_all_methods(SettingsActivityClass, "fillItems", SettingsAccountInfoHook(self))
            if hooked:
                self.log("Hooked SettingsActivity.fillItems")
            self.hook_all_methods(SettingsActivityClass, "onClick", SettingsAccountOnClickHook(self))
            self.hook_all_methods(SettingsActivityClass, "onLongClick", SettingsAccountOnLongClickHook(self))

            SettingCellClass = JavaClass.forName("org.telegram.ui.SettingsActivity$SettingCell")
            if SettingCellClass:
                hooked = self.hook_all_methods(SettingCellClass, "set", SettingsIconsHook(self))
                if hooked:
                    self.log("Hooked SettingsActivity.SettingCell.set")

        FragmentContextViewClass = JavaClass.forName("org.telegram.ui.Components.FragmentContextView")
        if FragmentContextViewClass:
            self.hook_all_constructors(FragmentContextViewClass, AudioPlayerTopBarHook(self))
            self.hook_all_methods(FragmentContextViewClass, "checkCreateView", AudioPlayerTopBarHook(self))
            self.log("Hooked FragmentContextView")

        DialogsActivityClass = JavaClass.forName("org.telegram.ui.DialogsActivity")
        if DialogsActivityClass:
            hooked = self.hook_all_methods(
                DialogsActivityClass, "updateStoriesPosting", ComposeButtonHook(self)
            )
            if hooked:
                self.log("Hooked DialogsActivity.updateStoriesPosting")
            hooked = self.hook_all_methods(
                DialogsActivityClass, "updateFloatingButtonVisibility", ComposeButtonHook(self)
            )
            if hooked:
                self.log("Hooked DialogsActivity.updateFloatingButtonVisibility")
            # Re-apply the pencil when returning to the dialogs list (the app
            # re-sets its icon only on createView/notification events).
            hooked = self.hook_all_methods(DialogsActivityClass, "onResume", ComposeButtonHook(self))
            if hooked:
                self.log("Hooked DialogsActivity.onResume")

        PhotoAdapterClass = JavaClass.forName(
            "org.telegram.ui.Components.ChatAttachAlertPhotoLayout$PhotoAttachAdapter"
        )
        if PhotoAdapterClass:
            hooked = self.hook_all_methods(PhotoAdapterClass, "getItemCount", CameraTileSingleCellHook(self))
            if hooked:
                self.log("Hooked ChatAttachAlertPhotoLayout.PhotoAttachAdapter.getItemCount")

        ChatInputContainerClass = JavaClass.forName("org.telegram.ui.Components.chat.ChatInputViewsContainer")
        if ChatInputContainerClass:
            try:
                self.hook_all_methods(ChatInputContainerClass, "setInputIslandBubbleDrawable", ChatInputBubbleHook(self))
                self.hook_all_methods(ChatInputContainerClass, "setUnderKeyboardBackgroundDrawable", ChatInputUnderKeyboardHook(self))
                self.hook_all_methods(ChatInputContainerClass, "checkViewsPositions", ChatInputContainerPositionHook(self))
                self.hook_all_methods(ChatInputContainerClass, "dispatchDraw", ChatInputDispatchDrawHook(self))
            except Exception as e:
                print("Failed to hook ChatInputContainer", e)
            
        ChatActivityTopPanelClass = JavaClass.forName("org.telegram.ui.Components.ChatActivityTopPanelLayout")
        if ChatActivityTopPanelClass:
            try:
                self.hook_all_methods(ChatActivityTopPanelClass, "dispatchDraw", ChatActivityTopPanelBoundsHook(self))
                self.hook_all_methods(ChatActivityTopPanelClass, "setPadding", TopPanelPaddingHook(self))
            except Exception as e:
                print("Failed to hook ChatActivityTopPanelLayout", e)
            
        ActionBarClass = JavaClass.forName("org.telegram.ui.ActionBar.ActionBar")
        if ActionBarClass:
            try:
                self.hook_all_methods(ActionBarClass, "setupGlass", ActionBarSetupGlassHook(self))
            except Exception as e:
                print("Failed to hook ActionBar", e)


