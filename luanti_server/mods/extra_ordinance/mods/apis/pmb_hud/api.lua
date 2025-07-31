
function pmb_hud.change_hud(player, tag, def)
    local pi = pmb_hud.check_player(player)
    local pitag = pi.id[tag]
    if pitag and pitag.id then
        if not pitag.def then pitag.def = {} end
        for stat, value in pairs(def) do
            if pitag.def[stat] ~= nil and tostring(pitag.def[stat]) ~= tostring(value) then
                player:hud_change(pitag.id, stat, value)
                pitag.def[stat] = value
            end
        end
        return
    end
end

function pmb_hud.add_hud(player, tag, def, no_replace)
    local pi = pmb_hud.check_player(player)
    local pitag = pi.id[tag]
    if pitag then
        if pitag.id ~= nil then
            if no_replace then
                pmb_hud.change_hud(player, tag, def)
                return
            else
                pmb_hud.remove_hud(player, tag)
            end
        end
    end
    pi.id[tag] = {
        id = COMPAT.hud_add(player, def),
        def = def,
    }
end

function pmb_hud.has_hud(player, tag)
    local pi = pmb_hud.check_player(player)
    local pitag = pi.id[tag]
    if pitag then
        return pitag.id ~= nil
    end
end

local _debug_pl = {}
function pmb_hud.debug(player, text, color)
    local pi = _debug_pl[player]
    if not pi then pi = {}; _debug_pl[player] = pi end
    if color then text = minetest.colorize(color, text) end
    table.insert(pi, text)
end

minetest.register_globalstep(function(dtime)
    for player, list in pairs(_debug_pl) do
        local text = table.concat(list, "\n")
        if pmb_hud.has_hud(player, ":debug") then
            pmb_hud.change_hud(player, ":debug", {
                text = text
            })
        else
            pmb_hud.add_hud(player, ":debug", {
                type = "text",
                text = text,
                position = {x=0.02, y=0.2},
                alignment = {x=1, y=1},
                z_index = 1999
            })
        end
        _debug_pl[player] = nil
    end
end)

function pmb_hud.remove_hud(player, tag)
    local pi = pmb_hud.check_player(player)
    local pitag = pi.id[tag]
    if pmb_hud._builtin[tag] then
        player:hud_set_flags({
            [pmb_hud._builtin[tag]._flagname] = false,
        })
        return
    end

    if pitag and pitag.id then
        player:hud_remove(pitag.id)
        pitag.id = nil
        return
    end
end

function pmb_hud.reset_hud(player, tag)
    local pi = pmb_hud.check_player(player)
    local pitag = pi.id[tag]
    if pmb_hud.default[tag] then
        if (not pitag) or (not pitag.id) then
            pmb_hud.add_hud(player, tag, pmb_hud.default[tag])
            return
        end
    end

    if pmb_hud._builtin[tag] then
        player:hud_set_flags({
            [pmb_hud._builtin[tag]._flagname] = true,
        })
        return
    end

    if pitag and pitag.id then
        pmb_hud.remove_hud(player, tag)
        return
    end
end