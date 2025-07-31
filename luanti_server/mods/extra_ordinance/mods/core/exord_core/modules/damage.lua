
exord_core.NumSet = {}
exord_core.NumSet.__type = "numset"

function exord_core.NumSet.__mul(self, b)
    local copy = self:copy()
    local is_num = type(b) == "number"
    local from = ((not is_num) and b.__type == "numset" and b.tab) or b
    for dname, dval in pairs(copy.tab) do
        if (not is_num) and from[dname] then
            copy.tab[dname] = dval * from[dname]
        elseif is_num then
            copy.tab[dname] = dval * from
        end
    end
    return copy
end

function exord_core.NumSet.__add(self, b)
    local copy = self:copy()
    local from = (b.__type == "numset" and b.tab) or b
    for dname, dval in pairs(copy.tab) do
        if from[dname] then
            copy.tab[dname] = dval + from[dname]
        end
    end
    return copy
end

function exord_core.NumSet.__call(self)
end

local __meta = {
    __index = exord_core.NumSet,
    __mul = exord_core.NumSet.__mul,
    __add = exord_core.NumSet.__add,
    __call = exord_core.NumSet.__call,
}

--- non-meta functions

function exord_core.NumSet.copy(self)
    local c = setmetatable({tab={}}, __meta)
    c.tab = {}
    for k, v in pairs(self.tab) do
        c.tab[k] = v
    end
    return c
end

function exord_core.NumSet.new(from_table)
    local ret = setmetatable({tab={}}, __meta)
    if from_table then
        for k, v in pairs(from_table) do
            ret.tab[k] = v
        end
    end
    return ret
end

function exord_core.NumSet.get_total(self)
    local total = 0
    for k, v in pairs(self.tab) do total = total + v end
    return total
end

function exord_core.NumSet.get_max(self)
    local max; for k, v in pairs(self.tab) do
        if (not max) or v > max then max = v end
    end return max
end

function exord_core.NumSet.get_min(self)
    local min; for k, v in pairs(self.tab) do
        if (not min) or v < min then min = v end
    end return min
end

local _OFFSET = vector.new(0.01, 2, 0.01)
-- distance_factor: toward 0 is "sharper" and, 1 = linear, >2 is parabolic
function exord_core.damage_radius(pos, radius, NumSet, source, distance_factor, max_targets)
    if radius == 0 then return 0 end
    local objects = minetest.get_objects_inside_radius(pos, radius)
    table.sort(objects, function(a, b)
        return exord_core.dist2(a:get_pos(), pos) < exord_core.dist2(b:get_pos(), pos)
    end)

    local target_count = 0
    if not distance_factor then distance_factor = 0 end
    for i, object in ipairs(objects) do repeat
        if object == source then break end
        if target_count >= max_targets then break end
        local p = object and object:get_pos()
        --#TODO: REPLACE WITH BETTER METHOD, SINCE THIS ONLY CARES ABOUT "air" NODES
        if not minetest.line_of_sight(pos + _OFFSET, p + _OFFSET) then break end
        local ent = (pos ~= nil) and object:get_luaentity()
        if (not ent) or (not ent._on_damage) then break end
        local d2 = exord_core.dist2(p, pos)
        local unit_dist = d2 / (radius^2) -- 0 is on the point, 1 is at the edge
        local f = 1 - (unit_dist ^ distance_factor)
        local dmgset = NumSet * f
        if ent._exord_armor then
            dmgset = dmgset * ent._exord_armor
        end
        if exord_core.damage_entity(ent, dmgset, source) then
            target_count = target_count + 1
        end
    until true end
    return target_count
end

function exord_core.damage_entity(entity, NumSet, source)
    if entity and entity.get_luaentity then entity = entity:get_luaentity() end
    if (not entity) or (not entity._on_damage) then return end
    return entity:_on_damage(NumSet:get_max(), source) ~= false
end
