
--  add hand tool
core.override_item("", {
    wield_image = "blank.png",
	range = 300,
	wield_scale = { x = 1, y = 1, z = 1 },
	tool_capabilities = {
		full_punch_interval = 0.0,
		max_drop_level = 0,
		groupcaps = {},
		damage_groups = {},
	}
})

-- use table insert to force it to the back of the list
table.insert(core.registered_on_joinplayers, 1, function(player, last_login)
    player:set_minimap_modes({{type = "off", label = " "}}, 0)
	player:set_sky({
		base_color = "#000000",
		type = "regular",
		clouds = false,
		sky_color = {
			day_sky = "#000000",
			day_horizon = "#000000",
			dawn_sky = "#000000",
			dawn_horizon = "#000000",
			night_sky = "#000000",
			night_horizon = "#000000",
			indoors = "#000000",
			fog_sun_tint = "#000000",
			fog_moon_tint = "#000000",
			fog_tint_type = "custom",
		}
	})
    player:set_physics_override({sneak = false})
    player:set_sun({
        visible = false,
        sunrise_visible = false,
    })
    player:set_moon({
        visible = false,
    })
    player:set_stars({
        visible = false,
    })
    player:set_inventory_formspec("")
    player:set_formspec_prepend("")
end)
