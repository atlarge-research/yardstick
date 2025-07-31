local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)
local S = minetest.get_translator(mod_name)

pmb_hud = {}

pmb_hud.pl = {}
local pl = pmb_hud.pl

function pmb_hud.check_player(player)
    if not pl[player] then
        pl[player] = {
            id={},
        }
    end
    return pl[player]
end

pmb_hud.default = {
    hotbar_bg = {
        type = "image",
        alignment = {x=0, y=1},
        position = {x=0.5, y=1},
        name = "health_bg",
        text = "pmb_hotbar_bg.png",
        z_index = 10,
        scale = {x = 1, y = 1},
        offset = {x = 0, y = -91},
    }
}

pmb_hud._builtin = {
    health = {
        _flagname = "healthbar",
        type = "statbar",
        position = {x=0.5, y=1},
        name = "health",
        text = "pmb_health_full.png",
        text2 = "pmb_health_empty.png",
        z_index = 11,
        number = 13,
        item = 20,
        size = {x = 24, y = 24},
        direction = 1,
        offset = {x = -18 - 30 - 8, y = -93}
    },
    breath = {
        _flagname = "breathbar",
        type = "statbar",
        position = {x=0.5, y=1},
        name = "breath",
        text = "pmb_breath_full.png",
        text2 = "pmb_breath_empty.png",
        z_index = 11,
        number = 13,
        item = 20,
        size = {x = 24, y = 24},
        -- direction = 1,
        offset = {x = 18 + 30 - 16, y = -93},
    },
}

dofile(mod_path .. "/api.lua")

if minetest.get_modpath("age_of_mending") then
    dofile(mod_path .. "/aom_compat.lua")
end
