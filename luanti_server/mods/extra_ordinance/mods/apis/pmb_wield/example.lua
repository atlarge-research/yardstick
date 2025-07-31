local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)
local S = minetest.get_translator(mod_name)


do ---
local t = 0
local has_ph
minetest.register_tool("pmb_wield:test", {
    description = S("Test item"),
    groups = { combat = 2, not_in_creative_inventory = 1 },

    on_select = function(stack, player)
        has_ph = minetest.get_modpath("playerphysics") and true
        if has_ph then
            playerphysics.add_physics_factor(player, "gravity", "pmb_wield:test", 0.5)
            playerphysics.add_physics_factor(player, "speed", "pmb_wield:test", 1.5)
        end
    end,
    on_deselect = function(stack, player)
        if has_ph then
            playerphysics.remove_physics_factor(player, "gravity", "pmb_wield:test")
            playerphysics.remove_physics_factor(player, "speed", "pmb_wield:test")
        end
        return ItemStack("pmb_wield:test 1 "..math.random(20, 50000))
    end,
    on_step = function(stack, player, dtime)
        local vel_y = player:get_velocity().y
        player:add_velocity(vector.new(0, math.max(vel_y * -0.05, 0), 0))
        t = t + dtime if t > 1 then t = t - 1 else return end
        minetest.log("tick")
        return ItemStack("pmb_wield:test 1 "..math.random(59000, 60000))
    end,

    _pmb_combat = {
        base_damage = {
            cut = 5,
            blunt = 2,
        },
        max_base_damage = 5,

        on_attacking = function(w)
        end,
        on_step = function(w, dtime)
        end,
    },

    inventory_image = "pmb_stone_axe.png",
    tool_capabilities = {
        full_punch_interval = 1,
        groupcaps = {
            choppy = {
                max_drop_level = 3,
                times = { 8 },
                uses = 0,
            },
            snappy = {
                max_drop_level = 3,
                times = { 0.25 },
                uses = 0,
            },
        },
        damage_groups = {
            slash=2,
            blunt=2,
        },
    },
})
end