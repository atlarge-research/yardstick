local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)
local S = minetest.get_translator(mod_name)

local type_colors = {
    boolean = "#f58",
    number = "#4af",
    string = "#2f5",
}

aom_settings.register_setting("sound_menu_volume", 1, "Menu volume")
aom_settings.register_setting("menu_technical_names", false, "Use technical names of settings")

-- store the hashes that get sent through the form fields, to authenticate that
-- the fields actually came from the player we think it did
local hashes = {}

local function generate_hash(player)
    hashes[player] = string.sub(minetest.sha1(math.random()), 1, 16)
    return hashes[player]
end

local function check_hash(player, fields)
    if not hashes[player] then return false end
    return fields._auth_hash == hashes[player]
end

-- -- -- MAIN HANDLER FUNCTIONS
function aom_settings.form.get_settings_page_header(fs, title, desc, flags)
    if not flags then flags = {} end
    table.insert(fs, "box[5,0;13,12;#111111e0]")
    -- delete all button
    if not flags.no_reset then
        table.insert(fs,    "box[5.5,9.1;2,1.2;#ff556680]")
        table.insert(fs, "button[5.6,9.2;1.8,1;reset_all;"..S("reset all").."]")
    end
    -- back buttons
    table.insert(fs, "set_focus[back;false]")
    table.insert(fs, "button[5.1,0.1;1.8,1;back;"..S("back").."]")
    -- SETTINGS label
    table.insert(fs, "label[8,1.2;"..desc.."]")
    table.insert(fs, "style_type[label;font_size=*0.8;textcolor=#aaa]")
    table.insert(fs, "label[5.2,2.75;Inputting an invalid value]")
    table.insert(fs, "label[5.2,3;will reset it to its default value.]")
    table.insert(fs, "style_type[label;font_size=*2;textcolor=#fea;font=bold]")
    table.insert(fs, "label[8,0.7;"..title.."]")
end

local settingpages = {}
settingpages.player = {
    title = "PLAYER SETTINGS",
    desc = "These are local to your player character on this world and are sent to the server.",
}
settingpages.server = {
    title = "SERVER SETTINGS",
    desc = "SERVER settings, these change the server settings and require permissions.",
    flags = {no_reset=true}
}

function aom_settings.form.get_settings_list(fs, player, pagename)
    if not fs then fs = {} end
    local pi = aom_settings.check_player(player)
    -- reset some styles
    table.insert(fs, "style_type[label;font_size=*0.8;textcolor=#ddd;font=normal]")
    table.insert(fs, "style_type[image_button;border=false]")

    local last_col = "#ddd" -- avoid styling elements when you don't need to
    local y = 0.5
    local rowindex = 1
    local technical_names = aom_settings.get_setting(player, "menu_technical_names", false)
    for catname, settinglist in pairs(aom_settings.registered_settings_by_category[pagename] or {}) do
        local color = "#111"
        local ysize = #settinglist * 1.2 + 1.1
        table.insert(fs, "box[0.5,"..(y+0.2)..";7,"..ysize..";"..color.."]")
        table.insert(fs, "style_type[label;font_size=*1.5;textcolor=#fff;font=bold]")
        table.insert(fs, "label[1,"..tostring(y+0.6)..";"..catname.."]")
        table.insert(fs, "style_type[label;font_size=*0.8;textcolor=#ddd;font=normal]")
        rowindex = rowindex * -1
        y = y + 1.3
        local cat_y = y
        for i, def in ipairs(settinglist) do
            local settingname = def.name
            local desc = (technical_names and settingname) or def.desc or settingname
            local currentval = aom_settings.get_setting(player, settingname)
            currentval = minetest.formspec_escape(tostring(currentval))
            -- color based on type
            local col = type_colors[def.type] or "#ddd"
            if col ~= last_col then
                table.insert(fs, "style_type[label;textcolor="..col.."]")
            end
            local is_default = aom_settings.is_setting_default(player, settingname)
            table.insert(fs, "label[0.75,"..(y+0.3)..";"..def.type.."]")

            if pi.last_setting_focus == settingname then
                table.insert(fs, "set_focus[".."set:"..settingname..";true]")
                table.insert(fs, "field[1.75,"..(y)..";5,0.8;set:"..settingname..";"..desc..";"..currentval.."]")
                table.insert(fs, "field_close_on_enter[set:"..settingname..";false]")
            else
                table.insert(fs, "button[1.75,"..(y)..";5,0.8;focus:"..settingname..";"..currentval.."]")
                table.insert(fs, "field_close_on_enter[focus:"..settingname..";false]")
            end
            if pi.last_setting_set == "set:"..def.name then
                table.insert(fs, "image[6.2,"..(y+0.15)..";0.5,0.5;aom_settings_tick.png]")
            end
            if not is_default then
                table.insert(fs, "image_button[6.8,"..(y+0.15)..";0.5,0.5;".."aom_settings_reset.png;".."reset:"..settingname.."; ]")
            end
            y = y + 1.2
        end
        y = cat_y -- reset to start of this category again
        -- labels showing the description of the setting
        table.insert(fs, "style_type[label;font_size=*1.0;textcolor=#fff;font=normal]")
        for i, def in ipairs(settinglist) do
            local settingname = def.name
            local desc = (technical_names and settingname) or def.desc or settingname
            if pi.last_setting_focus == settingname then
            else
                table.insert(fs, "label[1.75,"..(y-0.2)..";"..desc.."]")
            end
            y = y + 1.2
        end
    end
    return fs, y
end

function aom_settings.form.get_settings_page(fs, player, pagename, page_header)
    local pi = aom_settings.check_player(player)

    -- get heading page
    if not page_header then return end

    aom_settings.form.add_formspec_defaults(fs)

    aom_settings.form.get_settings_page_header(fs, page_header.title, page_header.desc, page_header.flags)

    -- send the auth hash too, so that it can authenticate this player when they set stuff
    table.insert(fs, "field[100.75,0;5,0.8;_auth_hash;AUTH HASH;"..generate_hash(player).."]")

    -- main container start
    table.insert(fs, "box[8.5,1.5;8,10;#333333c0]")
    table.insert(fs, "scroll_container[8.5,1.5;8,10;scroll;vertical;0.1]")

    local y = 0
    fs, y = aom_settings.form.get_settings_list(fs, player, pagename)

    table.insert(fs, "scroll_container_end[]")
    -- scroll container
    local maxscroll = y * 10 - 70
    table.insert(fs, "scrollbaroptions[arrows=hide;smallstep=10"..
        ";thumbsize=10;max="..tostring(maxscroll).."]")
    table.insert(fs, "scrollbar[8,1.5;0.5,10;vertical;scroll;"..tostring(pi.last_scroll or 0).."]")
end

function aom_settings.form.handle_settings_page_action(player, pagename, fields)
    local pi = aom_settings.check_player(player)

    if fields.quit then return end

    -- security check to prevent impersonation
    if (hashes[player] ~= nil) and not check_hash(player, fields) then
        minetest.chat_send_player(
            player:get_player_name(),
            "WARNING: SOMEONE JUST TRIED TO IMPERSONATE YOU IN ORDER TO CHANGE SETTINGS ON YOUR BEHALF. THIS WAS BLOCKED.")
        return
    end
    hashes[player] = nil -- don't let it hang around

    if fields.back then
        pi.last_setting_set = nil
        aom_settings.form.do_sound_click(player, "aom_settings_click")
        return aom_settings.form.show_page(player, "main")
    end
    if fields.reset_all then
        pi.settings = {}
        pi.last_setting_set = nil
        aom_settings.save_player(player)
        minetest.sound_play("aom_settings_click", {
            gain = 1 * aom_settings.get_setting(player, "sound_menu_volume"),
            pitch = 0.8,
            to_player = player:get_player_name(),
        })
        return aom_settings.form.show_page(player, pagename)
    end

    if fields.scroll then
        local scroll = minetest.explode_scrollbar_event(fields.scroll)
        pi.last_scroll = ((scroll.type == "CHG") and scroll.value) or pi.last_scroll
    end

    local refresh = false

    for key, value in pairs(fields) do repeat
        local action = string.split(key, ":")
        if (not action) or #action < 2 then break end
        local setting = aom_settings.registered_settings[action[2]]
        if action[1] == "focus" then
            pi.last_setting_focus = action[2]
            refresh = true
        elseif (setting ~= nil) and (value ~= "") then
            if action[1] == "reset" then
                aom_settings.set_setting(player or "nil", action[2], nil)
                aom_settings.form.show_page(player, pagename)
                minetest.sound_play("aom_settings_click", {
                    gain = 1 * aom_settings.get_setting(player, "sound_menu_volume"),
                    pitch = 0.8,
                    to_player = player:get_player_name(),
                })
            elseif key == fields.key_enter_field then
                aom_settings.form.do_sound_click(player, "aom_settings_click")
                pi.last_setting_set = key
                aom_settings.set_setting(player or "nil", action[2], value)
            end
        end
    until true end

    if fields.key_enter or refresh then
        aom_settings.form.show_page(player, pagename)
    end
end

-- -- -- END OF MAIN HANDLERS


-- -- -- CALLBACKS
-- SETTINGS MENU
aom_settings.form.register_page_process("player", function(fs, player, pagename, data)
    aom_settings.form.get_settings_page(fs, player, "player", settingpages.player)
end)

-- SETTINGS MENU
aom_settings.form.register_page_process("server", function(fs, player, pagename, data)
    aom_settings.form.get_settings_page(fs, player, "server", settingpages.server)
end)

