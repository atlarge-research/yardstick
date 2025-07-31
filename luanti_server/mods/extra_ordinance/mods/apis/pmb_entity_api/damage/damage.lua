

pmb_entity_api.damage = {}

local mod_path = minetest.get_modpath(minetest.get_current_modname())
dofile(mod_path .. DIR_DELIM .. "damage" .. DIR_DELIM .. "weapons.lua")

local me = pmb_entity_api.damage

me.knockback_mult = 3
me.knockback_ymult = 1.5



function pmb_entity_api.damage.do_knockback(self, puncher, time_from_last_punch, tool_capabilities, dir, damage, weapon)
    local weapon_knockback = 1
    if weapon then weapon_knockback = weapon.knockback or 1 end
    local mob_knockback = self._knockback or 1
    local v = self.object:get_velocity()
    dir = vector.multiply(dir, (weapon_knockback * mob_knockback * me.knockback_mult))
    dir.y = v.y + (weapon_knockback * mob_knockback * me.knockback_ymult)
    if v.y > 3 then dir.y = 0 end
    v = vector.add(v, dir)
    if v.y > 3 then v.y = 3 end
    self.object:set_velocity(v)
    return true
end

function pmb_entity_api.damage.deal(self, puncher, time_from_last_punch, tool_capabilities, dir, damage, weapon)
    if weapon and weapon.on_damage then
        weapon.on_damage(self, puncher, time_from_last_punch, tool_capabilities, dir, damage)
    end
    return true
end

function pmb_entity_api.damage.on_punch(self, puncher, time_from_last_punch, tool_capabilities, dir, damage)
    if (not damage) or damage <= 0 then return false end
    local weapon = pmb_entity_api.damage.get_puncher_weapon(puncher)
    local dealt_damage = pmb_entity_api.damage.deal(self, puncher, time_from_last_punch, tool_capabilities, dir, damage, weapon)
    pmb_entity_api.damage.do_knockback(self, puncher, time_from_last_punch, tool_capabilities, dir, damage, weapon)
end
