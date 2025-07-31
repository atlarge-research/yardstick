
pmb_entity_api.damage.weapon = {}

function pmb_entity_api.damage.get_weapon_default(name)
    return {
        name = name,
        knockback = 1,
        damage_groups = {},
        on_damage = function(self, puncher, time_from_last_punch, tool_capabilities, dir, damage) return false end,
    }
end

function pmb_entity_api.damage.get_damage_group(name, group)
    if pmb_entity_api.damage.weapon[name] then
        return pmb_entity_api.damage.weapon[name].damage_groups[group] or 0
    end
    return 0
end

function pmb_entity_api.damage.register_weapon(param)
    pmb_entity_api.damage.weapon[param.name] = param
end

function pmb_entity_api.damage.get_puncher_weapon(puncher)
    if not puncher then return false end
    local stack = puncher:get_wielded_item()
    if (not stack) or (stack:get_count()<=0) then return false end
    local name = stack:get_name()
    local def = pmb_entity_api.damage.weapon[name]
    if def then
        return def
    end
    return false
end
