
exord_core.excavation_site = {}


local cbox = {
    -0.3, 0,-0.3,
     0.3, 2, 0.3,
}
local sbox = {
    -1, 0,-1,
     1, 2, 1,
}

minetest.register_entity("exord_core:excavation_site", {
    initial_properties = {
        visual = "mesh",
        mesh = "exord_excavation_site.b3d",
        textures = {
            "polyhaven_metal_grid.jpg",
            "polyhaven_steel_container.jpg",
            "polyhaven_metal_sheets.jpg",
            "polyhaven_metal_plate.jpg",
        },
        use_texture_alpha = false,
        stepheight = 0,
        hp_max = 20,
        physical = true,
        collisionbox = cbox,
        selectionbox = sbox,
        pointable = false,
        damage_texture_modifier = "^[colorize:#ff9999:50",
        static_save = false,
        -- glow = 4,
        visual_size = vector.new(1, 1, 1),
    },
    _animations = {
        idle = {frames={x=0, y=0}, blend=0.2},
    },
	on_step = function(self, dtime)
	end,
    on_deactivate = function(self)
    end,
    on_activate = function(self, staticdata, dtime_s)
        pmb_entity_api.on_activate(self, staticdata, dtime_s)
    end,
})
