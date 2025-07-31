local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)
local S = minetest.get_translator(mod_name)

aom_settings.registered_settings = {}
aom_settings.registered_settings_array = {}
aom_settings.registered_settings_by_category = {}
aom_settings.player_meta = {}
aom_settings.server_settings = {}

do -- get settings persistently
local past_settings = aom_settings.mod_storage:get_string("server_settings")
if past_settings ~= "" then
    past_settings = minetest.deserialize(past_settings, true)
    if past_settings and type(past_settings) == "table" then
        aom_settings.server_settings = past_settings
    end
end
end

local pl = aom_settings.player_meta

-- set player meta so that settings are persistent
function aom_settings.save_player(player)
    local meta = player:get_meta()
    meta:set_string("aom_settings:settings", minetest.serialize(pl[player].settings))
end
-- set meta so that settings are persistent
function aom_settings.save_server()
    aom_settings.mod_storage:set_string("server_settings", minetest.serialize(aom_settings.server_settings))
end

-- make sure the player is tracked
function aom_settings.check_player(player)
    if not pl[player] then
        local meta = player:get_meta()
        -- COMPATIBILITY FIX: to remove in a40
        local old_data = meta:get_string("aom_igm:settings")
        if old_data ~= "" then
            meta:set_string("aom_settings:settings", old_data)
            meta:set_string("aom_igm:settings", "")
        end
        local deser = minetest.deserialize(meta:get_string("aom_settings:settings"), true)
        pl[player] = {
            settings = deser or {},
        }
        if deser then
            for i, v in pairs(pl[player].settings) do
                if not aom_settings.registered_settings[i] then
                    pl[player].settings[i] = nil
                end
            end
        end
        aom_settings.save_player(player)
    end
    return pl[player]
end

-- gets the player setting, or the default if not set
function aom_settings.get_setting(player, settingname, default)
    local setting = aom_settings.registered_settings[settingname]
    if not setting then return default end
    -- server settings
    if setting.menuname == "server" then
        local val = aom_settings.server_settings[settingname]
        if val == nil then val = setting.default end
        if val == nil then return default else return val end
    end
    if not minetest.is_player(player) then return end
    local pi = aom_settings.check_player(player)
    local plval = pi.settings[settingname]
    if plval == nil then plval = setting.default end
    return plval
end

-- true if this value is not set at all, even if it's the same actual value as default
function aom_settings.is_setting_default(player, settingname)
    local setting = aom_settings.registered_settings[settingname]
    if not setting then return true end
    -- server settings
    if setting.menuname == "server" then
        return (aom_settings.server_settings[settingname] == nil)
    end
    local pi = aom_settings.check_player(player)
    return (pi.settings[settingname] == nil)
end

-- don't let player set arbitrary values
local function sanitise_value(value, val_type)
    if type(value) == val_type then return value end
    if val_type == "number" then return tonumber(value) end
    if val_type == "boolean" then return (value == "true") or not (value == "false") end
end

local function try_set_server_setting(player, settingname, value)
    if player and not minetest.check_player_privs(player, "server") then return end
    local setting = aom_settings.registered_settings[settingname]
    if value ~= nil then
        value = sanitise_value(value, setting.type)
    end
    local old_value = aom_settings.server_settings[settingname]
    aom_settings.server_settings[settingname] = value
    aom_settings.save_server()
    local new_value = aom_settings.server_settings[settingname]
    if new_value == nil then new_value = setting.default end
    aom_settings.on_change_setting(player, settingname, new_value, old_value)
end

-- set a player setting with a raw value
function aom_settings.set_setting(player, settingname, value)
    local setting = aom_settings.registered_settings[settingname]
    if not setting then return nil end
    -- server settings handled differently
    if setting.menuname == "server" then
        return try_set_server_setting(player, settingname, value)
    end
    local pi = aom_settings.check_player(player)
    if value ~= nil then
        value = sanitise_value(value, setting.type)
    end
    local old_value = pl[player].settings[settingname]
    pi.settings[settingname] = value
    aom_settings.save_player(player)

    local plval = pl[player].settings[settingname]
    if plval == nil then plval = setting.default end
    aom_settings.on_change_setting(player, settingname, plval, old_value)
end

-- register a player setting, using type(default) as a type
function aom_settings.register_setting(name, default, desc, menuname)
    if not menuname then menuname = "player" end
    local already_registered = aom_settings.registered_settings[name]
    local def = {}
    if already_registered then def = already_registered end
    local t = type(default)
    def.name = name -- technical name of setting
    def.type = t -- datatype
    def.default = default -- default value
    def.desc = desc -- non-technical name
    def.menuname = menuname -- which menu the setting is in
    if already_registered then return end
    aom_settings.registered_settings[name] = def
    table.insert(aom_settings.registered_settings_array, aom_settings.registered_settings[name])
end

aom_settings.registered_on_change_setting = {}
-- runs when a setting for a player is changed --> callback(player, settingname, new_value, old_value)
function aom_settings.register_on_change_setting(settingname, callback)
    if not aom_settings.registered_on_change_setting[settingname] then aom_settings.registered_on_change_setting[settingname] = {} end
    table.insert(aom_settings.registered_on_change_setting[settingname], callback)
end

aom_settings.registered_on_change_any_setting = {}
-- runs when a setting for a player is changed --> callback(player, settingname, new_value, old_value)
function aom_settings.register_on_change_any_setting(callback)
    table.insert(aom_settings.registered_on_change_any_setting, callback)
end

function aom_settings.on_change_setting(player, settingname, new_value, old_value)
    for i, callback in ipairs(aom_settings.registered_on_change_any_setting) do
        callback(player, settingname, new_value, old_value)
    end
    for i, callback in ipairs(aom_settings.registered_on_change_setting[settingname] or {}) do
        callback(player, settingname, new_value, old_value)
    end
end

function aom_settings.sort_by_category()
    local cat = aom_settings.registered_settings_by_category
    for i, def in ipairs(aom_settings.registered_settings_array) do
        local catname = string.split(def.name, "_")[1] --(ΦωΦ)
        local menuname = def.menuname
        if not cat[menuname] then cat[menuname] = {} end
        if not cat[menuname][catname] then cat[menuname][catname] = {} end
        table.insert(cat[menuname][catname], def)
    end
end
minetest.register_on_mods_loaded(aom_settings.sort_by_category)


