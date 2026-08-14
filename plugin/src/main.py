from elyx import strings
from base_plugin import BasePlugin
from java.lang import Class as JavaClass

from .hooks import (
    IsBasePackOnlyHook,
    DialogCellOnDrawHook,
    DialogCellBuildLayoutHook,
    GetThemedColorHook,
    SendButtonOnDrawHook,
    SpringAnimationsHook,
    VoiceVideoAnimHook,
    ProfileLevelsHook,
    ImmersiveDrawerHook,
    SettingsAccountInfoHook,
    ComposeButtonHook,
    SettingsIconsHook,
    CameraTileSingleCellHook,
    WallpaperSourceDimHook,
    WallpaperColorDimHook,

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

            SettingCellClass = JavaClass.forName("org.telegram.ui.SettingsActivity$SettingCell")
            if SettingCellClass:
                hooked = self.hook_all_methods(SettingCellClass, "set", SettingsIconsHook(self))
                if hooked:
                    self.log("Hooked SettingsActivity.SettingCell.set")

        DialogsActivityClass = JavaClass.forName("org.telegram.ui.DialogsActivity")
        if DialogsActivityClass:
            hooked = self.hook_all_methods(
                DialogsActivityClass, "updateStoriesPosting", ComposeButtonHook(self)
            )
            if hooked:
                self.log("Hooked DialogsActivity.updateStoriesPosting")

        PhotoAdapterClass = JavaClass.forName(
            "org.telegram.ui.Components.ChatAttachAlertPhotoLayout$PhotoAttachAdapter"
        )
        if PhotoAdapterClass:
            hooked = self.hook_all_methods(PhotoAdapterClass, "getItemCount", CameraTileSingleCellHook(self))
            if hooked:
                self.log("Hooked ChatAttachAlertPhotoLayout.PhotoAttachAdapter.getItemCount")

        WallpaperProviderClass = JavaClass.forName(
            "org.telegram.ui.Components.chat.WallpaperBitmapProvider"
        )
        if WallpaperProviderClass:
            source_hook = WallpaperSourceDimHook(self)
            hooked = self.hook_all_methods(
                WallpaperProviderClass,
                "updateSourceFromBackgroundViewDrawable",
                source_hook,
            )
            if hooked:
                self.log("Hooked WallpaperBitmapProvider.updateSourceFromBackgroundViewDrawable")
            for method_name in ("getStatusBarColor", "getNavigationBarColor"):
                color_hook = WallpaperColorDimHook(self, source_hook)
                hooked = self.hook_all_methods(WallpaperProviderClass, method_name, color_hook)
                if hooked:
                    self.log(f"Hooked WallpaperBitmapProvider.{method_name}")


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


