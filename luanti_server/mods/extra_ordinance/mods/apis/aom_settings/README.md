
# aom_settings
Mirror of `aom_settings` from Age of Mending (AoM). This allows for world-level settings, and can be hooked into via `aom_ingame_menu` to give a GUI for changing your player or server settings. **This does provide a GUI for modifying settings**, but it is not accessible except by commands by default. These commands also are not accessible except to `server` privileges by default, but can be set so anyone can use the player settings menu. Use `/settings server` to access the server settings to change this. The normal way to integrate this into your game or mod is to provide a compatibiliy hook into this api from whatever formspec you desire. That can be done by using the functions listed below.

## Getting setting values
When getting a setting, use `aom_settings.get_setting(player, settingname, default)`. You can optionally specify a default, in which case if the setting doesn't exist and isn't set, this will be returned instead.

This allows you to have player based settings, which can be configurable ingame via formspecs (see: `aom_ingame_menu`).
```lua
local function play_music(player, track)
    local volume = 1
    if minetest.get_modpath("aom_settings") then
        volume = aom_settings.get_setting(player, "music_volume", 1)
    end
    if volume <= 0 then return end
    minetest.sound_play(track, {
        gain = volume,
        to_player = player:get_player_name(),
    })
end
```

## Register new settings
To register a setting, use `aom_settings.register_setting(settingname, default, non_technical_name)`. Settings are grouped by the first word, separated by `_` so; `item_pickup_distance` will be in the category `item` and `gameplay_node_drop_item` will be in the category `gameplay`.
```lua
aom_settings.register_setting("item_pickup_distance", 3, "Item pickup distance")
```
Setting a setting that **doesn't exist** will **do nothing and have no effect**; settings must be registered first. You may overwrite existing settings by registering them again.


## Server level settings
You can also set server level settings, and they are accessed in exactly the same way, except `nil` is passed for the player since it isn't needed. Passing `nil` as the player will force the setting to be set, otherwise if a player or a string is given, it will check auth with `minetest.check_player_privs(player, "server")`.
```lua
aom_settings.register_setting("debug_enabled", false, "Debug enabled", "server")
local debug = aom_settings.get_setting(nil, "debug_enabled", false)
```

**VERY IMPORTANT**: if making own setting GUI, it is important that some non-falsy value like `player or "nothing"` is given or else it is theoretically possible for a bad actor to set server settings by sending form fields. Similarly, sending a sha1 or some random value in the GUI formspec and checking for this as a second factor when submitting changes to settings is advisable for the same reason. See `aom_ingame_menu` for an example of this.


## Callbacks
These will be called when the setting changes value.

This can help if you need to change a local value or update something when a setting is changed; for example if music is playing, it might be helpful to fade the volume of the music to match the new value. Note that `old_value` can be nil if the setting was not set yet at the time, and so can `player` in the case of server settings. If a setting has been set to `nil`, `new_value` will be the default value rather than `nil`.
```lua
aom_settings.register_on_change_setting(settingname, function(player, settingname, new_value, old_value) end)
aom_settings.register_on_change_any_setting(function(player, settingname, new_value, old_value) end)
```

## Formspec

To show a settings page to a player, use the following. You need to provide a player object, *not* a name.
```lua
aom_settings.form.show_page(player, pagename)
-- pagename can be "player" or "server"
```

More pages can be registered as well. Like "server", these are seperate pages for settings. If you register settings in a completely different page, this is how you access those. This is not meant to be like tabs though you could use it that way. This requires providing a page header table, with `title` and `desc` fields.
```lua
local page_header = {
    title = "MY SETTINGS PAGE",
    desc = "These settings are special.",
}
aom_settings.form.register_page_process("my_page_name", function(fs, player, pagename, data)
    aom_settings.form.get_settings_page(fs, player, pagename, page_header)
end)
```
