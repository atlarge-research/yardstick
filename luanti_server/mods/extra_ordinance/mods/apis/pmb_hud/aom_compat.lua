

minetest.hud_replace_builtin("health", pmb_hud._builtin.health)

minetest.hud_replace_builtin("breath", pmb_hud._builtin.breath)

minetest.register_on_joinplayer(function(player)
    local pi = pmb_hud.check_player(player)
    player:hud_set_flags({
        minimap_radar = false,
    })
    pi.id.hotbar_bg = COMPAT.hud_add(player, pmb_hud.default.hotbar_bg)
end)
