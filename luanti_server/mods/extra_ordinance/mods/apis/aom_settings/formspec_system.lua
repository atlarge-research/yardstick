local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)
local S = minetest.get_translator(mod_name)

-- almost a copy of the aom_igm functionality in order to make our own formspecs
-- no, we can't depend, since that would be a dependency loop

aom_settings.form.registered_pages = {}

function aom_settings.form.do_sound_click(player, sound)
    minetest.sound_play((sound), {
        gain = 1 * aom_settings.get_setting(player, "sound_menu_volume", 1),
        to_player = player:get_player_name(),
    })
end

-- adds the usual default vals to the formspec
function aom_settings.form.add_formspec_defaults(fs)
    table.insert(fs, "formspec_version[6]")
    table.insert(fs, "size[24.00,12.0]")
    table.insert(fs, "no_prepend[]")
    table.insert(fs, "listcolors[#00000000;#00000000;#00000000;#111;#eee]")
    table.insert(fs, "bgcolor[#00000000]")
    table.insert(fs, "style_type[item_image_button;bgcolor=#fff;bgcolor_hovered=#fff;bgcolor_pressed=#fff]")
    table.insert(fs, "style_type[item_image_button;textcolor=#8c3f5d;border=false]")
    table.insert(fs, "style_type[button;bgimg=aom_inv_btn.png\\^\\[multiply:#616161;bgimg_middle=8;"..
    "bgimg_hovered=aom_inv_btn.png\\^\\[multiply:#616161;bgimg_pressed=aom_inv_btn_press.png\\^\\[multiply:#616161;"..
    "bgcolor_hovered=#eee;bgcolor_pressed=#fff]".."style_type[button;border=false]")
end

-- if returns false, cancels as if not allowed to show this
-- callback(player, pagename, fs_table) --> false or nil
function aom_settings.form.register_page_process(pagename, callback)
    if not aom_settings.form.registered_pages[pagename] then aom_settings.form.registered_pages[pagename] = {} end
    table.insert(aom_settings.form.registered_pages[pagename], callback)
end

-- returns false if not allowed to show this formspec
function aom_settings.form.get_formspec(player, pagename)
    local calls = aom_settings.form.registered_pages[pagename]
    if not calls then return false end
    local fs = {}
    local data = {}
    for i, callback in ipairs(calls) do
        local ret = callback(fs, player, pagename, data)
        if ret == false then return false end
    end
    return table.concat(fs, "")
end

-- interactions
minetest.register_on_player_receive_fields(function(player, formname, fields)
    if formname:sub(1,12) ~= "aom_settings" then return end
    local pagename = formname:split(":")[2] or ""
    return aom_settings.form.handle_settings_page_action(player, pagename, fields)
end)

-- show a page formspec
function aom_settings.form.show_page(player, pagename)
    if (not aom_settings.form.registered_pages[pagename])
    and (minetest.get_modpath("aom_igm") ~= nil) then
        -- if we don't have the page, try aom_igm instead
        return aom_igm.show_page(player, pagename)
    end
    local fs = aom_settings.form.get_formspec(player, pagename)
    if not fs then return false end
    minetest.show_formspec(player:get_player_name(), "aom_settings:" .. pagename, fs)
    return true
end

-- command allowing you to open menu
if not minetest.settings:get_bool("aom_settings_disable_command", false) then
    minetest.register_chatcommand("settings", {
        params = "",
        description = S("Opens the in game menu for aom_settings"),
        privs = {},
        func = function(name, param)
            local player = minetest.get_player_by_name(name)
            local privs = minetest.check_player_privs(player, "server")
            if (not privs) and not aom_settings.get_setting(nil, "menu_commands", false) then
                return false, S("Not allowed to view that page, or page doesn't exist.")
            end
            if (param == "server") then
                if not privs then
                    return false, S("Missing privilege: \"server\"")
                end
                if not aom_settings.form.show_page(player, "server") then
                    return false, S("Not allowed to view that page, or page doesn't exist.")
                end
            else
                if not aom_settings.form.show_page(player, "player") then
                    return false, S("Not allowed to view that page, or page doesn't exist.")
                end
            end
            return true
        end
    })
end
