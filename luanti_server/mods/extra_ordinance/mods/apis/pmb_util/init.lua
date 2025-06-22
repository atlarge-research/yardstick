local mod_name = minetest.get_current_modname()
local mod_path = minetest.get_modpath(mod_name)
local S = minetest.get_translator(mod_name)


pmb_util = {}
pmb_util.player = {}


minetest.register_on_joinplayer(function(ObjectRef, last_login)
    pmb_util.player[ObjectRef] = {}
end)
minetest.register_on_leaveplayer(function(ObjectRef, timed_out)
    pmb_util.player[ObjectRef] = nil
end)


dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "math.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "time.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "on_look.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "tools_and_hand_range.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "rotate_node.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "only_place_on.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "itemdrop.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "has_adjacent.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "give_to.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "make_shapes.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "output_node_list.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "on_change_wielditem.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "set_fov.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "prevent_digging.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "server_info.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "abm_tracker.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "nodelight_unfck.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "manual_wield_image.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "item_use.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "formspec_actions.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "try_rightclick.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "find_biome.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "item_display.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "player_force_set_velocity.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "player_force_move_pos.lua")
dofile(mod_path .. DIR_DELIM .. "scripts" .. DIR_DELIM .. "collision_box_to_vertex.lua")

-- nodes
dofile(mod_path .. DIR_DELIM .. "nodes" .. DIR_DELIM .. "air_lights.lua")
dofile(mod_path .. DIR_DELIM .. "nodes" .. DIR_DELIM .. "various.lua")
