
-- stop player dropping or moving items
minetest.register_allow_player_inventory_action(function(player, action, inventory, inventory_info)
    return 0
end)

local function play_confirm_sound(player)
    minetest.sound_play("exord_igm_click", {
        to_player = player:get_player_name(),
        gain = 1,
    }, true)
end

function exord_core.form_on_fields_select_loadout(form, player, formname, fields)
    if not minetest.is_player(player) then return end
    local pi = exord_core.check_player(player)
    for field, val in pairs(fields) do
        local len = string.len(field)
        local split = string.split(field, ":")
        if split and split[1] == "select_loadout" then
            local i = tonumber(split[3])
            local slot = tonumber(split[2])
            local def = exord_core.get_loadout_by_uid(i)
            if def and slot and i then
                play_confirm_sound(player)
                exord_core.player_select_loadout(player, slot, def.name, pi)
            end
        end
    end
    exord_core.player_apply_selected_loadout(player, pi, false)
end

local function form_move_difficulty_selection(form, player, difficulty_name)
    local selector = form:get_element_by_id("diff:selection")
    local new_cont = form:get_element_by_id("cdiff:"..difficulty_name)
    if (not selector) or not new_cont then return end
    new_cont:add_child(selector)
end

function exord_core.form_on_fields_select_difficulty(form, player, formname, fields)
    if not minetest.is_player(player) then return end
    if exord_core.gamestate ~= 0 then
        minetest.sound_play("exord_core_beep_notallowed", {
            gain = 0.8,
            to_player = player:get_player_name()
        }, true)
        return
    end
    local pi = exord_core.check_player(player)
    for field, val in pairs(fields) do
        local split = string.split(field, ":")
        if split and split[1] == "diff" then
            local mode = split[2]
            if mode and exord_core.difficulty_modes[mode] then
                exord_core.difficulty = exord_core.difficulty_modes[mode]
                -- core.log("changed to new difficulty")
                play_confirm_sound(player)
                form_move_difficulty_selection(form, player, mode)
            end
        end
    end
    exord_core.player_apply_selected_loadout(player, pi, false)
end

function exord_core.form_on_fields_button(form, player, formname, fields)
    if fields.show_stats then
        exord_core.show_stats_form_to_player(player, false)
        play_confirm_sound(player)
    elseif fields.show_luanti_limits then
        exord_core._form_luanti_limits:show_form(player, false)
        play_confirm_sound(player)
    elseif fields.show_controls then
        exord_core._form_controls:show_form(player, false)
        play_confirm_sound(player)
    elseif fields.show_licenses then
        exord_core._form_credits:show_form(player, false)
        play_confirm_sound(player)
    end
end

function exord_core.init_formspec(player)
    local pi = exord_core.check_player(player)
    local form = exord_bform.element.form:new({24, 12}, 6, nil)
    form:add_children({
        exord_bform.element.container.new({24, 12}, {1,0}, "main"):add_children({
            exord_bform.element.listcolors.new("#f00", "#f00", "#f00"),
            exord_bform.element.listcolors.new("#00000010", nil, "#0ff"),
            exord_bform.element.custom.new(nil, "bgcolor", {"bgcolor[#00000050;neither]"}),
            exord_bform.element.custom.new(nil, nil, {
                "style_type[item_image_button;bgcolor=#fff;bgcolor_hovered=#fff;bgcolor_pressed=#fff]",
                "style_type[item_image_button;textcolor=#8c3f5d;border=false]",
                "style_type[item_image_button;bgimg=exord_core_gui_slot_bg.png;bgimg_middle=8;",
                "bgimg_hovered=exord_core_gui_slot_bg_hover.png;bgimg_pressed=exord_core_gui_slot_bg_press.png;",
                "bgcolor_hovered=#fff;bgcolor_pressed=#fff]".."style_type[button;border=false]",

                "style_type[button;bgimg=exord_core_gui_slot_bg.png^\\[opacity:100;bgimg_middle=8;",
                "bgimg_hovered=exord_core_gui_slot_bg_hover.png;bgimg_pressed=exord_core_gui_slot_bg_press.png;",
                "bgcolor_hovered=#fff;bgcolor_pressed=#fff]".."style_type[button;border=false]",
            }),

            exord_bform.element.container.new({6, 10}, {0,1}, "left"):set_expand(true):add_children({
                exord_bform.element.background9.new(
                    nil, "exord_core_gui_panel_bg.png", false, 250
                ):set_fill({0,0}):set_ignore_spacing(true),
                exord_bform.element.container.new({6,9}, {0,1}, "difficulty_buttons"):add_children({
                    exord_bform.element.container.new({5, 0.8}, {0,1}, "difficulty_title"):add_children({
                        exord_bform.element.custom.new({6, 0.5}, "difficulty_title_label", {
                            "label[0.3,0.5;Difficulty Settings]"
                        })
                    }),
                    exord_bform.element.container.new({5,1.5}, {1,0}, "cdiff:easy"):add_children({
                        exord_bform.element.button.new({3,1.5}, "TOO EASY", "diff:easy", exord_core.form_on_fields_select_difficulty),
                    }),
                    exord_bform.element.container.new({5,1.5}, {1,0}, "cdiff:normal"):add_children({
                        exord_bform.element.button.new({3,1.5}, "NORMAL", "diff:normal", exord_core.form_on_fields_select_difficulty),
                        exord_bform.element.image.new("exord_core_gui_arrow.png", {0.5,0.5}, nil, "diff:selection"):set_offset({0.2,0.5}),
                    }),
                    exord_bform.element.container.new({5,1.5}, {1,0}, "cdiff:hard"):add_children({
                        exord_bform.element.button.new({3,1.5}, "KINDA HARD", "diff:hard", exord_core.form_on_fields_select_difficulty),
                    }),
                    exord_bform.element.container.new({5,1.5}, {1,0}, "cdiff:fun_hard"):add_children({
                        exord_bform.element.button.new({3,1.5}, "FUN HARD", "diff:fun_hard", exord_core.form_on_fields_select_difficulty),
                    }),
                    exord_bform.element.container.new({5,1.5}, {1,0}, "cdiff:very_hard"):add_children({
                        exord_bform.element.button.new({3,1.5}, "NOT FUN HARD", "diff:very_hard", exord_core.form_on_fields_select_difficulty),
                    }),
                }):set_offset({1, 0.7}),
            }):set_absolute_pos({0,0}),

            exord_bform.element.container.new({6, 10}, {0,1}, "middle"):set_expand(true):add_children({
                exord_bform.element.background9.new(
                    nil, "exord_core_gui_panel_bg_small.png", false, 28
                ):set_fill({0,0}):set_ignore_spacing(true),
                exord_bform.element.container.new({5,1.5}, {0,1}, "general_buttons"):add_children({
                    exord_bform.element.button.new({3,0.7}, "Show stats", "show_stats", exord_core.form_on_fields_button):set_spacing({0, 0.2}),
                    exord_bform.element.button.new({3,0.7}, "Show controls", "show_controls", exord_core.form_on_fields_button):set_spacing({0, 0.2}),
                    exord_bform.element.button.new({3,0.7}, "Bugs?", "show_luanti_limits", exord_core.form_on_fields_button):set_spacing({0, 0.2}),
                    exord_bform.element.button.new({3,0.7}, "Credits", "show_licenses", exord_core.form_on_fields_button):set_spacing({0, 0.2}),
                }):set_offset({1.5, 1}),
            }):set_absolute_pos({6,0}),

            exord_bform.element.container.new({12, 10}, {0,1}, "right"):set_expand(true):add_children({
                exord_bform.element.background9.new(
                    nil, "exord_core_gui_panel_bg.png", false, 250
                ):set_fill({0,0}):set_ignore_spacing(true),
                exord_bform.element.container.new({6, 0.8}, {0,1}, "loadouts_title"):add_children({
                    exord_bform.element.custom.new({6, 0.3}, "loadouts_title_label", {
                        "label[0.3,0.3;Loadouts get set when respawning or completing an objective]",
                        "label[0.3,0.6;or during pre-game time.]",
                    })
                }):set_offset({1, 0.7}),
                exord_bform.element.container.new({12, 11}, {1,0}, "loadouts_list"):add_children({
                    exord_bform.element.container.new({1.8, 6}, {0,1}, "loadout_1"),
                    exord_bform.element.container.new({1.8, 6}, {0,1}, "loadout_2"),
                    exord_bform.element.container.new({1.8, 6}, {0,1}, "loadout_3"),
                    exord_bform.element.container.new({1.8, 6}, {0,1}, "loadout_4"),
                    exord_bform.element.container.new({1.8, 6}, {0,1}, "loadout_5"),
                    exord_bform.element.container.new({1.8, 6}, {0,1}, "loadout_6"),
                }):set_offset({1, 1}),
            }):set_absolute_pos({12,0}),
        }),
    }):set_params({
        auth_enabled = true,
        send_on_update = true,
    })
    form.on_changed = function(self, sources)
    end
    for slot = 1, 6 do repeat
        local loadouts = exord_core.get_loadouts_for_slot(slot)
        if #loadouts == 0 then break end
        local slot_elem = assert(form:get_element_by_id("loadout_" .. slot))
        local selected = exord_core.player_get_selected_loadout_def(player, slot, pi)
        local sel_item = selected and selected.item or ""
        slot_elem:add_children({
            exord_bform.element.background9.new({0.6, 0.6 + (1.6) * (#loadouts+1) + 0.1},
                "[fill:1x1:0,0:#2f2c28", false, ""
            ):set_ignore_spacing(true):set_offset({0.5, 0}),
            exord_bform.element.image.new("exord_core_gui_slot_bg_select.png", {2, 2}, nil, nil
            ):set_ignore_spacing(true):set_offset({-0.2, -0.2}),
            exord_bform.element.item_image.new(sel_item, {1.5,1.5}, "selected_loadout:"..slot
            ):set_spacing({0.3, 0.6}),
        })
        for i, def in ipairs(loadouts) do
            slot_elem:add_child(
                exord_bform.element.item_image_button.new(
                    def.item, {1.5,1.5},
                    "", "select_loadout:"..slot..":"..def.uid,
                    exord_core.form_on_fields_select_loadout
                ):set_spacing({0, 0.12})
            )
        end
    until true end

    exord_bform.set_inventory_form(player, form)
end

minetest.register_on_joinplayer(function(player, last_login)
    exord_core.init_formspec(player)
end)


local stats_form = exord_bform.element.form:new({24, 12}, 6, "stats_form")
stats_form:add_children({
    exord_bform.element.container.new({24, 12}, {1,0}, "main"):add_children({
        exord_bform.element.listcolors.new("#f00", "#f00", "#f00"),
        exord_bform.element.listcolors.new("#00000010", nil, "#0ff"),
        exord_bform.element.custom.new(nil, "bgcolor", {"bgcolor[#00000050;neither]"}),

        exord_bform.element.container.new({6, 10}, {0,1}, "left"):set_expand(true):add_children({
            exord_bform.element.background9.new(
                nil, "blank.png^[noalpha^[colorize:#111:255^[opacity:200", false, 28
            ):set_fill({0,0}):set_ignore_spacing(true),
            exord_bform.element.container.new({6, 0.6}, {0,1}, "player_list_title"):add_children({
                exord_bform.element.custom.new({5, 0.0}, "player_list_title_label", {
                    "label[0.3,0.2;Player List]"
                }),
                exord_bform.element.custom.new({5, 0.0}, nil, {
                    "label[1.6,0.5;", "name", "]"
                }),
                exord_bform.element.custom.new({5, 0.0}, nil, {
                    "label[3.5,0.5;", "kills", "]"
                }),
                exord_bform.element.custom.new({5, 0.0}, nil, {
                    "label[4.2,0.5;", "obj", "]"
                }):set_visible(false),
                exord_bform.element.custom.new({5, 0.0}, nil, {
                    "label[4.5,0.5;", "deaths", "]"
                }),
            }),
            exord_bform.element.container.new({5, 11}, {0,1}, "player_list"):set_offset({0.1, 0}),
        }):set_absolute_pos({0,0}),
        exord_bform.element.container.new({6, 10}, {0,1}, "middle"):set_expand(true):add_children({
            exord_bform.element.background9.new(
                nil, "blank.png^[noalpha^[colorize:#111:255^[opacity:50", false, 28
            ):set_fill({0,0}):set_ignore_spacing(true)
        }):set_absolute_pos({6,0}),
        exord_bform.element.container.new({12, 10}, {0,1}, "right"):set_expand(true):add_children({
            exord_bform.element.background9.new(
                {0,0}, "blank.png^[noalpha^[colorize:#111:255^[opacity:50", false, 28
            ):set_fill({0,0}):set_ignore_spacing(true),
        }):set_absolute_pos({12,0}),
    }),
}):set_params({
    auth_enabled = false,
    send_on_update = false,
})

-- not sure if works
function exord_core.get_stats_fragment(update)
    if update then
        for i, player in ipairs(exord_player.get_non_spectator_players()) do
            exord_core.update_player_stats_form_elem(player)
        end
    end
    local list = assert(stats_form:get_element_by_id("player_list"))
    local fs = {}
    local dt = {}
    list:render(fs, dt)
    return list:render_children(fs, dt)
end

function exord_core.show_stats_form_to_player(player, update)
    if update then
        exord_core.update_stats_form()
    end
    stats_form:show_form(player, update)
end

function exord_core.update_stats_form()
    for i, player in ipairs(exord_player.get_non_spectator_players()) do
        exord_core.update_player_stats_form_elem(player)
    end
end

local _t = 0
minetest.register_globalstep(function(dtime)
    _t = _t - dtime; if _t > 0 then return end; _t = _t + 1
    exord_core.update_stats_form()
end)

function exord_core.show_stats_form(update)
    if update then
        exord_core.update_stats_form()
    end
    for i, player in ipairs(minetest.get_connected_players()) do
        stats_form:show_form(player, update)
    end
end

function exord_core.close_stats_form()
    for i, player in ipairs(minetest.get_connected_players()) do
        minetest.close_formspec(player:get_player_name(), "stats_form")
    end
end

local function _label_render(self, fs, data, ...)
    table.insert(fs, "label[")
    table.insert(fs, self._x or 1)
    table.insert(fs, ",0.5;")
    table.insert(fs, self._text or "nil")
    table.insert(fs, "]")
    return fs
end

function exord_core.update_player_stats_form_elem(player)
    local name = player:get_player_name()
    local list = assert(stats_form:get_element_by_id("player_list"))
    local elem = stats_form:get_element_by_id("player_stat:"..name)
    local sanname = string.sub(name, 1, math.min(16, string.len(name)))
    if not elem then
        elem = exord_bform.element.container.new({6, 1.2}, {0,1}, "player_stat:"..name):add_children({
            exord_bform.element.background9.new(
                {5.8, 1.0}, "blank.png^[noalpha^[colorize:#222:255^[opacity:200", false, 28
            ):set_ignore_spacing(true),
            exord_bform.element.image.new("exord_core_gui_player_icon.png", {1,1}, nil, nil
            ):set_ignore_spacing(true),
            exord_bform.element.custom.new({5, 0.0}, "player_stat:"..name..":name", {
                "label[1.5,0.5;", sanname, "]"
            }),
            exord_bform.element.custom.new({5, 0.0}, "player_stat:"..name..":kills", nil, _label_render
            ):set_params({_x=3.5, _text = "0"}),
            exord_bform.element.custom.new({5, 0.0}, "player_stat:"..name..":objectives", nil, _label_render
            ):set_params({_x=4.2, _text = "0"}):set_visible(false), -- disabled
            exord_bform.element.custom.new({5, 0.0}, "player_stat:"..name..":deaths", nil, _label_render
            ):set_params({_x=4.6, _text = "0"}),
        }):set_offset({0, 0.1})
        list:add_child(elem)
        list:get_root():init_children()
    end
    if elem then
        SIGNAL("on_player_stats_elem_update", player, elem)
    end
end

function exord_core.remove_player_stats_elem(player)
    local name = player:get_player_name()
    local list = assert(stats_form:get_element_by_id("player_list"))
    local elem = stats_form:get_element_by_id("player_stat:"..name)
    if not elem then return end
    list:remove_child(elem)
end

minetest.register_on_joinplayer(function(player, last_login)
    exord_core.update_player_stats_form_elem(player)
end)

minetest.register_on_leaveplayer(function(player, timed_out)
    exord_core.remove_player_stats_elem(player)
end)



exord_core._form_luanti_limits = exord_bform.element.form:new({24, 12}, 6, "luanti_limits")
exord_core._form_luanti_limits:add_children({
    exord_bform.element.container.new({24, 12}, {1,0}, "main"):add_children({
        exord_bform.element.listcolors.new("#f00", "#f00", "#f00"),
        exord_bform.element.listcolors.new("#00000010", nil, "#0ff"),
        exord_bform.element.custom.new(nil, "bgcolor", {"bgcolor[#00000050;neither]"}),

        exord_bform.element.container.new({24, 12}, {0,1}, "main_text"):set_expand(true):add_children({
            exord_bform.element.custom.new({0, 0.0}, nil, {
                "scroll_container[0,0;24,12;scroll;vertical;0.1]"
            }),
            exord_bform.element.background9.new(
                nil, "blank.png^[noalpha^[colorize:#111:255^[opacity:240", false, 28
            ):set_fill({0,0}):set_ignore_spacing(true),
        }):set_absolute_pos({0,0}),
    }),
}):set_params({
    auth_enabled = false,
    send_on_update = false,
})

local _luanti_limitations = {
    "",
    "Luanti is amazing, it's just very focused on voxel sandbox games, and isn't (yet) a generalised engine. Extra Ordinance is NOT what you would typically make with this engine, and as such this game runs into the engine's limitations FAST. That means many things here are just completely broken, and there's nothing I can do to fix it except fork the engine, and I don't have the skill, time nor patience for that. So, below is a list of things that are impossible for me to fix, but which are obviously broken.",

    "",
    "Of course, everything else is actually my fault :)",

    "\n \nEntire sections of the world phasing in and out of existence",
    "Luanti doesn't provide anything for controlling which mapblocks are shown to a client, I can only send them and hope, vainly.",

    "After blowing up a huge part of the map, it just stays unchanged until you move the camera in the right way",
    "Same as above, can't control it.",

    "You can enable third person and it breaks *everything*",
    "Literally can't even know if you've enabled it. So yeah. I tried to make a system that shows a particle with a big warning on it, that you can only see when you're in third person. Hopefully that's enough that at least people know they shouldn't use third person mode, instead of being left wondering why everything is broken.",

    "Movement is slow and lagged",
    "The camera is stuck to the physical player object, and can't be moved seperately, so I had to make a seperate, server-controlled (laggy) player character. That's the mech you see. The actual real player is floating in the sky.",

    "The camera angle is unpredictable",
    "Since the camera is a player, and the player is 'owned' by the client, not the server, I can't control it smoothly and without latency. It's a compromise; I could attach the player to another camera-controller object and introduce even more latency - making it a singleplayer or LAN only game, or keep it like this, having it be initially responsive but then it does some weird stuff sometimes.",

    "Right click to reload",
    "You can't map arbitrary keys, so it was that or the [sneak], [jump] or [aux1] keys. It ends up being more convenient to use right click for this at least, once you get used to it.",

    "The lighting looks blurry or blotchy",
    "Baked voxel lighting always looks bad. I can't use (or rely on) shadows to their full potential either, since they are too slow and flicker when you move the camera, and are too performance heavy.",

    "Sometimes bullets and explosions are invisible",
    "Things (particles) with transparency are hidden when they are behind transparent objects, meaning waypoints and other effects hide particle effects and make them invisible. This has been a limitation for years.",
}

local function format_linelen(t, n)
    local fp = {}
    local fplines = 1
    local fplen = 0
    for wn, word in ipairs(string.split(t, " ", true)) do
        local wlen = string.len(word)
        if fplen + wlen > n then
            fplines = fplines + 1
            fplen = 0
            table.insert(fp, "\n")
        elseif wn > 1 then
            table.insert(fp, " ")
        end
        fplen = fplen + wlen
        table.insert(fp, word)
    end
    return table.concat(fp), fplines
end

do
    local main_text = assert(exord_core._form_luanti_limits:get_element_by_id("main_text"))
    local line_len_max = 80
    for i = 1, #_luanti_limitations, 2 do
        local p, lp = format_linelen(_luanti_limitations[i], line_len_max)
        local e, le = format_linelen(_luanti_limitations[i+1], line_len_max)
        local lines = math.max(lp, le)

        local split_p = string.split(p, "\n")
        local split_e = string.split(e, "\n")
        for k = 1, #split_p do
            main_text:add_children({
                exord_bform.element.container.new({12, 0.3}, {0,1}, nil):add_children({
                    exord_bform.element.custom.new({5, 0.0}, nil, {
                        "label[2,0.5;", minetest.colorize("#fd9", minetest.formspec_escape(split_p[k] or "")), "]"
                    }),
                }),
            })
        end
        for k = 1, #split_e do
            main_text:add_children({
                exord_bform.element.container.new({12, 0.3}, {0,1}, nil):add_children({
                    exord_bform.element.custom.new({5, 0.0}, nil, {
                        "label[1,0.5;", minetest.colorize("#eee", minetest.formspec_escape(split_e[k] or "")), "]"
                    }),
                }),
            })
        end
        main_text:add_children({
            exord_bform.element.spacer.new({12, 0.2}, nil, nil)
        })
    end
    main_text:add_child(exord_bform.element.custom.new({5, 0.0}, nil, {
        "scroll_container_end[]",
        "scrollbaroptions[arrows=hide;smallstep=10"..
        ";thumbsize=50;max=60]",
        "scrollbar[0,0;0.5,12;vertical;scroll;0]"
    }))
end


exord_core._form_controls = exord_bform.element.form:new({24, 12}, 6, "controls")
exord_core._form_controls:add_children({
    exord_bform.element.container.new({24, 12}, {1,0}, "main"):add_children({
        exord_bform.element.listcolors.new("#f00", "#f00", "#f00"),
        exord_bform.element.listcolors.new("#00000010", nil, "#0ff"),
        exord_bform.element.custom.new(nil, "bgcolor", {"bgcolor[#00000050;neither]"}),
        exord_bform.element.custom.new(nil, nil, {
            "style_type[label;font=mono]",
        }),

        exord_bform.element.container.new({24, 12}, {0,1}, "main_text"):set_expand(true):add_children({
            exord_bform.element.background9.new(
                nil, "blank.png^[noalpha^[colorize:#111:255^[opacity:240", false, 28
            ):set_fill({0,0}):set_ignore_spacing(true),
            exord_bform.element.container.new({12, 0.5}, {0,1}, nil):add_children({
                exord_bform.element.custom.new({5, 0.0}, nil, {
                    "label[1.5,0.5;", minetest.colorize("#ff9", minetest.formspec_escape(
                        "CONTROLS"
                    )), "]"
                }),
            }),
        }):set_absolute_pos({0,0}),
    }),
}):set_params({
    auth_enabled = false,
    send_on_update = false,
})

local _form_controls = {
    "Movement with [up] [down] [left] [right] as usual (default is W S A D)",
    "Look with [mouse]",
    "",
    "[dig]      (LMB)           Fire weapons",
    "[jump]     (space)         Use special (dash etc)",
    "[sneak]    (left shift)    Fire slot 1 (coaxial MG etc)",
    "[aux1]     (E)             Show compass to next objective",
    "[place]    (RMB)           Reload current weapon",
}

do
    local main_text = assert(exord_core._form_controls:get_element_by_id("main_text"))
    for i, line in ipairs(_form_controls) do
        main_text:add_children({
            exord_bform.element.container.new({12, 0.4}, {0,1}, nil):add_children({
                exord_bform.element.custom.new({5, 0.0}, nil, {
                    "label[2,1;", minetest.colorize("#eee", minetest.formspec_escape(line)), "]"
                }),
            }),
        })
    end
end


exord_core._form_credits = exord_bform.element.form:new({24, 12}, 6, "credits")
exord_core._form_credits:add_children({
    exord_bform.element.container.new({24, 12}, {1,0}, "main"):add_children({
        exord_bform.element.listcolors.new("#f00", "#f00", "#f00"),
        exord_bform.element.listcolors.new("#00000010", nil, "#0ff"),
        exord_bform.element.custom.new(nil, "bgcolor", {"bgcolor[#00000050;neither]"}),

        exord_bform.element.container.new({24, 12}, {0,1}, "main_text"):set_expand(true):add_children({
            exord_bform.element.custom.new({24, 12}, "scroll_area", {
                "scroll_container[0,0;24,12;scroll;vertical;0.1]"
            }),
            exord_bform.element.custom.new({5, 0.0}, nil, {
                "scroll_container_end[]",
                "scrollbaroptions[arrows=hide;smallstep=10"..
                ";thumbsize=80;max=1000]",
                "scrollbar[0,0;0.5,12;vertical;scroll;0]"
            }),
            exord_bform.element.background9.new(
                nil, "blank.png^[noalpha^[colorize:#111:255^[opacity:240", false, 28
            ):set_fill({0,0}):set_ignore_spacing(true),
        }):set_absolute_pos({0,0}),
    }),
}):set_params({
    auth_enabled = false,
    send_on_update = false,
})

local _credits_broad = {
    "Broad Credits",
    minetest.colorize("#fd7", "Sumi"),
    "   Game design, game programming, item textures, most apis, all models,",
    "   animations, all voice lines, and many of the sounds (see below for details),",
    "   all GUI elements",
    "",
    minetest.colorize("#fd7", "Various Freesound.org Users"),
    "   Almost all gun sounds, including most of the reload sounds, all music,",
    "   a few other sounds like the radio sound",
    "",
    minetest.colorize("#fd7", "Polyhaven.com"),
    "   All of the high resolution textures for terrain",
    "",
    minetest.colorize("#fd7", "Magmi.Soundtracks (freesound.org)"),
    "   The 'action' soundtrack for when taking the last objective until winning the match",
    "   and the main track played in the background",
    "",
    minetest.colorize("#888", "License and ownership details can be found below in verbose format."),
    "",
}

minetest.register_on_mods_loaded(function()
    local mods = minetest.get_modnames()
    local media_licenses = {}
    for i, modname in ipairs(mods) do
        local path = minetest.get_modpath(modname)
        local licensefile = io.open(path .. "/LICENSE", "r")
        if licensefile then
            local text = licensefile:read("a")
            local split = string.split(text, "===\nMedia Licenses", false, 2)
            text = split[2] or ""
            local sections = string.split(text, "===", false)
            for k, section in ipairs(sections) do
                table.insert(media_licenses, section)
            end
        end
    end

    local y = 0.5
    local fs = {}
    for k, line in ipairs(_credits_broad) do
        table.insert(fs, "label[1.5,"..y..";")
        table.insert(fs, minetest.formspec_escape(line))
        table.insert(fs, "]")
        y = y + 0.3
    end

    for i, section in ipairs(media_licenses) do repeat
        if section == "" then break end
        for k, line in ipairs(string.split(section, "\n", false)) do
            table.insert(fs, "label[1,"..y..";")
            table.insert(fs, minetest.formspec_escape(line))
            table.insert(fs, "]")
            y = y + 0.3
        end
        y = y + 0.4
    until true end

    local elem = assert(exord_core._form_credits:get_element_by_id("scroll_area"))
    elem:add_child(
        exord_bform.element.custom.new(
            {0,0}, "licenses",
            {table.concat(fs)}
        )
    )
end)

-- PREPEND
local col = "#b09f71"
exord_bform.get_form("global_prepend"):add_children({
    -- remove the ugly square box menu bg
    exord_bform.element.custom.new(nil, "bgcolor", {
        "bgcolor[#00000000;neither]",
    }),
    -- style the buttons in the menu
    exord_bform.element.custom.new(nil, "buttonstyle", {
        "style_type[button;bgimg=bform_btn.png\\^\\[multiply:"..col..";bgimg_middle=8;",
        "bgimg_hovered=bform_btn.png\\^\\[multiply:"..col..";bgimg_pressed=bform_btn_press.png\\^\\[multiply:"..col..";",
        "bgcolor_hovered=#eee;bgcolor_pressed=#fff]",
        "style_type[button;border=false]",
    }),
    -- add 9 patch bg
    exord_bform.element.background9.new(nil, "bform_bg.png^[multiply:#4d4539^bform_bg_outline.png", true, 28),
    -- you can't use `label[]` in prepends, because minetest says no
    exord_bform.element.custom.new(nil, "version_notice", {
        "hypertext[0.4,5.2;6,1;test;<style color=#ba9158>",
        "Extra Ordinance",
        "</style>",
        "]",
    }),
})
