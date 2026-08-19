from base_plugin import MethodHook
from hook_utils import get_private_field
from java.lang import Class as JavaClass


class SettingsAccountInfoHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin

    def after_hooked_method(self, param):
        if not self.plugin.get_setting("settings_account_info", False):
            return

        try:
            items = param.args[0]
            if items is None or items.isEmpty():
                return
                
            activity = param.thisObject
            
            # Check if we already added it (to avoid duplicates on refresh)
            for i in range(items.size()):
                item = items.get(i)
                if getattr(item, "id", 0) == 1001:
                    return

            user_config = activity.getUserConfig()
            user_id = int(user_config.getClientUserId())
            full = activity.getMessagesController().getUserFull(user_id)
            user = activity.getMessagesController().getUser(user_id)
            
            # Respect ExteraGram "Hide phone number" setting
            try:
                from com.exteragram.messenger import ExteraConfig
                hide_phone = ExteraConfig.getHidePhoneNumber()
            except Exception:
                hide_phone = False

            phone = getattr(user, "phone", None)
            if not phone or hide_phone:
                phone = None
            else:
                phone = "+" + str(phone)
                
            username = getattr(user, "username", None)
            if username:
                username = "@" + str(username)
            else:
                username = None
                
            about = None
            if full is not None and getattr(full, "about", None):
                about = str(full.about)
                
            from org.telegram.ui.Components import UItem
            from org.telegram.messenger import LocaleController, R
            
            insert_idx = -1
            for i in range(items.size()):
                item = items.get(i)
                if getattr(item, "id", 0) == -1:
                    insert_idx = i
                    break
                    
            if insert_idx == -1:
                for i in range(items.size()):
                    item = items.get(i)
                    if getattr(item, "viewType", -1) == 188:
                        insert_idx = i + 1
                        break
                        
            if insert_idx == -1:
                insert_idx = 1
                
            try:
                from org.telegram.ui.Cells import TextDetailSettingsCell
                TextDetailSettingsCellClass = TextDetailSettingsCell
            except Exception:
                TextDetailSettingsCellClass = None

            def create_account_item(item_id, label, value, need_divider=True):
                if TextDetailSettingsCellClass is not None:
                    try:
                        context = activity.getContext()
                        cell = TextDetailSettingsCellClass(context)
                        cell.setTextAndValue(value, label, need_divider)
                        item = UItem.asCustom(item_id, cell)
                        return item
                    except Exception:
                        pass
                
                return UItem.asSettingsCell(item_id, label, value)

            account_title = LocaleController.getString("Account", R.string.Account)
            phone_title = LocaleController.getString("PhoneNumber", R.string.PhoneNumber)
            username_title = LocaleController.getString("Username", R.string.Username)
            bio_title = LocaleController.getString("UserBio", R.string.UserBio)

            account_items = []
            account_items.append(UItem.asHeader(account_title))
            if phone is not None:
                account_items.append(create_account_item(1001, phone_title, phone, True))
            if username is not None:
                account_items.append(create_account_item(1002, username_title, username, True))
            account_items.append(create_account_item(1003, "ID", str(user_id), about is not None))
            if about is not None:
                account_items.append(create_account_item(1004, bio_title, about, False))
            account_items.append(UItem.asShadow(None))
            
            for item in reversed(account_items):
                items.add(insert_idx, item)
                
        except Exception:
            pass


class SettingsAccountOnClickHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin

    def before_hooked_method(self, param):
        if not self.plugin.get_setting("settings_account_info", False):
            return

        try:
            item = param.args[0]
            if item is None:
                return
                
            item_id = getattr(item, "id", 0)
            if item_id not in (1001, 1002, 1003, 1004):
                return
                
            activity = param.thisObject
            from org.telegram.messenger import AndroidUtilities, LocaleController, R
            from org.telegram.ui.Components import BulletinFactory

            if item_id == 1001:
                from org.telegram.ui import ActionIntroActivity
                phone_type = getattr(ActionIntroActivity, "ACTION_TYPE_CHANGE_PHONE_NUMBER", None)
                phone_type = 3 if phone_type is None else int(phone_type)
                activity.presentFragment(ActionIntroActivity(phone_type))
                param.setResult(None)
            elif item_id == 1002:
                from org.telegram.ui import ChangeUsernameActivity
                activity.presentFragment(ChangeUsernameActivity())
                param.setResult(None)
            elif item_id == 1003:
                user_config = activity.getUserConfig()
                user_id_str = str(user_config.getClientUserId())
                AndroidUtilities.addToClipboard(user_id_str)
                msg = LocaleController.getString("TextCopied", R.string.TextCopied)
                BulletinFactory.of(activity).createCopyBulletin(msg).show()
                param.setResult(None)
            elif item_id == 1004:
                from org.telegram.ui import UserInfoActivity
                activity.presentFragment(UserInfoActivity())
                param.setResult(None)
        except Exception:
            pass


class SettingsAccountOnLongClickHook(MethodHook):
    def __init__(self, plugin):
        self.plugin = plugin

    def before_hooked_method(self, param):
        if not self.plugin.get_setting("settings_account_info", False):
            return

        try:
            item = param.args[0]
            if item is None:
                return
                
            item_id = getattr(item, "id", 0)
            if item_id not in (1001, 1002, 1003, 1004):
                return
                
            activity = param.thisObject
            user_config = activity.getUserConfig()
            user_id = int(user_config.getClientUserId())
            full = activity.getMessagesController().getUserFull(user_id)
            user = activity.getMessagesController().getUser(user_id)

            from org.telegram.messenger import AndroidUtilities, LocaleController, R
            from org.telegram.ui.Components import BulletinFactory

            to_copy = None
            bulletin_msg = LocaleController.getString("TextCopied", R.string.TextCopied)

            if item_id == 1001:
                phone = getattr(user, "phone", None)
                if phone:
                    to_copy = "+" + str(phone)
                    bulletin_msg = LocaleController.getString("PhoneCopied", R.string.PhoneCopied)
            elif item_id == 1002:
                username = getattr(user, "username", None)
                if username:
                    to_copy = "@" + str(username)
                    bulletin_msg = LocaleController.getString("UsernameCopied", R.string.UsernameCopied)
            elif item_id == 1003:
                to_copy = str(user_id)
            elif item_id == 1004:
                if full and getattr(full, "about", None):
                    to_copy = str(full.about)

            if to_copy:
                AndroidUtilities.addToClipboard(to_copy)
                BulletinFactory.of(activity).createCopyBulletin(bulletin_msg).show()

            param.setResult(True)
        except Exception:
            pass
