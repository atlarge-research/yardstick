pmb_util.manual_wield_image = {}

local pl = {}

local has_compatlib = minetest.get_modpath("compatlib") ~= nil
local function hud_add(player, def)
    if has_compatlib then
        return COMPAT.hud_add(player, def)
    else return player:hud_add(def) end
end

local function new_hud(player)
    pl[player].hud_id = hud_add(player, {
        type = "image",
        alignment = {x=0, y=-1},
        position = {x=0.5, y=1},
        name = "pmb_util:manual_wield_image",
        text = "blank.png",
        z_index = -1000,
        scale = {x = 4, y = 4},
        offset = {x = 0, y = 0},
    })
end

local function check_player(player)
    if not pl[player] then
        pl[player] = {
            hud_id = nil,
            last_gui_scale = 0.1,
        }
        new_hud(player)
    end

end

function pmb_util.manual_wield_image.set_image(player, image_name, params)
    check_player(player)

    player:hud_change(pl[player].hud_id, "text", image_name)

    if params then
        for param, val in pairs(params) do
            player:hud_change(pl[player].hud_id, param, val)
        end
    end
end

-- minetest.register_on_joinplayer(function(player, last_login)
--     pmb_util.manual_wield_image.set_image(player, "pmb_manual_hud_testrig.png")
-- end)

local t = 0
local on_globalstep = function(dtime)
    if t > 0 then t = t - dtime return else t = 1 end

    for i, player in ipairs(minetest.get_connected_players()) do
        local window = minetest.get_player_window_information(player:get_player_name())
        repeat
            if not window then break end
            check_player(player)
            -- minetest.log(dump(window))
            if not pl[player].hud_id then break end
            if not window.size then break end

            local ratio = math.min(
                window.size.y / 800,
                window.size.x / 800
            )

            player:hud_change(pl[player].hud_id, "scale", {
                x = 4 * ratio,
                y = 4 * ratio,
            })
        until true
    end
end
minetest.register_globalstep(on_globalstep)
