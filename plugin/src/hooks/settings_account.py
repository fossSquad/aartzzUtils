from base_plugin import MethodHook
from hook_utils import get_private_field


class SettingsAccountInfoHook(MethodHook):
    _marker = "\nID: "

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
                phone = None  # hide the row entirely if phone is hidden
            else:
                phone = "+" + str(phone)
                
            username = getattr(user, "username", None)
            if username:
                username = "@" + str(username)
            else:
                username = None  # no username — skip the row
                
            about = None
            if full is not None and getattr(full, "about", None):
                about = str(full.about)
                
            from org.telegram.ui.Components import UItem
            
            # Find the insertion index — right before the first section (e.g. ExteraGram settings)
            insert_idx = -1
            for i in range(items.size()):
                item = items.get(i)
                if getattr(item, "id", 0) == -1:  # Preferences item
                    insert_idx = i
                    break
                    
            if insert_idx == -1:
                for i in range(items.size()):
                    item = items.get(i)
                    if getattr(item, "viewType", -1) == 188:  # custom shadow for topView
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
                        # Instantiate the custom cell with the activity context
                        context = activity.getContext()
                        cell = TextDetailSettingsCellClass(context)
                        # Top text (big) is the value, bottom text (small) is the label
                        cell.setTextAndValue(value, label, need_divider)
                        item = UItem.asCustom(item_id, cell)
                        return item
                    except Exception:
                        pass
                
                # Fallback
                return UItem.asSettingsCell(item_id, label, value)

            account_items = []
            account_items.append(UItem.asHeader("Акаунт"))
            if phone is not None:
                account_items.append(create_account_item(1001, "Номер телефона", phone, True))
            if username is not None:
                account_items.append(create_account_item(1002, "Ім'я користувача", username, True))
            account_items.append(create_account_item(1003, "ID", str(user_id), about is not None))
            if about is not None:
                account_items.append(create_account_item(1004, "Про себе", about, False))
            account_items.append(UItem.asShadow(None))
            
            # Insert them
            for item in reversed(account_items):
                items.add(insert_idx, item)
                
        except Exception:
            pass
