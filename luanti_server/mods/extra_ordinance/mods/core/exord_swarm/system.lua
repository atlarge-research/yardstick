
local UP = vector.new(0,1,0)

exord_swarm.burrow_time_min = 1

local perlin_cost_add = PerlinNoise({
    spread = {x = 12, y = 900000, z = 12},
    seed = 748774,
    octaves = 1,
    persist = 0.1,
    lacunarity = 2.2,
    offset = 0.5,
    scale = 0.5,
}) exord_swarm.perlin_cost_add = perlin_cost_add

exord_swarm.pathfinding_options = exord_mobpath.Options.new({
    -- TRAVERSAL = function(p1, p2) return true end,
    -- BEST_GUESS_SORT = function(a_node, b_node) return (a_node.H < b_node.H) end,
    max_search = 300,
    BEST_GUESS_SORT = function(a_node, b_node)
        return a_node.H + math.min(10, a_node.G) < b_node.H + math.min(10, b_node.G)
    end,
    G = function(p1, p2, opt) -- cost from last node
        local node = minetest.get_node_or_nil(p2)
        local extra_cost = node and minetest.get_item_group(node.name, "traversible_extra_cost") or 0
        -- avoid walls
        local nodes = minetest.find_nodes_in_area(
            vector.offset(p2, -3, 0,-3),
            vector.offset(p2,  3, 0, 3),
            "group:traversible_extra_cost"
        )
        extra_cost = extra_cost + math.min(4, #nodes*2)

        nodes = minetest.find_nodes_in_area(
            vector.offset(p2, -2, -1,-2),
            vector.offset(p2,  2, -1, 2),
            "group:traversible_floor_extra_cost", true
        )
        local biggest_val = 0
        for nodename, list in pairs(nodes) do
            local groupval = minetest.get_item_group(nodename, "traversible_floor_extra_cost")
            local val = groupval
            if biggest_val < val then
                biggest_val = val
            end
        end
        extra_cost = extra_cost + biggest_val

        if opt.path_perlin_offset then
            local nv1 = perlin_cost_add:get_3d(p2 + opt.path_perlin_offset)
            extra_cost = extra_cost*(1+nv1) + (nv1)*4
        end
        return exord_mobpath.dist2(p1, p2) + (extra_cost)^2
    end,
    H = function(p, target)
        return exord_mobpath.dist2(p, target)
    end, -- distance or heuristic cost from target
    adjacent = { -- list of offsets to try to traverse
        vector.new( 1, 0, 0),
        vector.new(-1, 0, 0),
        vector.new( 0, 0, 1),
        vector.new( 0, 0,-1),
        -- vector.new( 1, 0, 1),
        -- vector.new(-1, 0,-1),
        -- vector.new(-1, 0, 1),
        -- vector.new( 1, 0,-1),
    }
})
-- cached metatable stuff
local _options_meta = {__index = exord_swarm.pathfinding_options}

function exord_swarm.debug_particle(pos, color, time, vel, size)
    do return end
    minetest.add_particle({
        size = size or 2, pos = pos,
        texture = "blank.png^[noalpha^[colorize:"..(color or "#fff")..":255",
        velocity = vel or vector.new(0, 0, 0),expirationtime = time, glow = 14,
    })
end

function exord_swarm.on_step(self, dtime)
    self._path_cooldown = (self._path_cooldown or 0) - dtime
    self._path_steal_cooldown = (self._path_steal_cooldown or 0) - dtime
    self._get_leader_cooldown = (self._get_leader_cooldown or 0) - dtime
end

local _leader_area = vector.new(14, 1, 14)

function exord_swarm.promote_to_leader(self)
    self._exord_is_leader = true
end

function exord_swarm.demote_from_leader(self, new_leader)
    self._exord_is_leader = false
    if new_leader then
        self._exord_leader = new_leader
    end
end

function exord_swarm.new_leader(pos)
    local nearby_objects = minetest.get_objects_in_area(pos - _leader_area, pos + _leader_area)
    local closest_to_target
    local closest_d2_to_target
    local swarm = {}
    for i, object in ipairs(nearby_objects) do
        local ent = object and object:get_luaentity()
        if ent and ent._exord_can_be_leader and ent._pmb_target then
            local d2 = exord_core.dist2(object:get_pos(), ent._pmb_target:get_pos())
            if (not closest_d2_to_target) or (d2 < closest_d2_to_target) then
                closest_d2_to_target = d2
                closest_to_target = ent
            end
        end
        if ent then
            table.insert(swarm, ent)
        end
    end
    local new_leader = closest_to_target
    if not new_leader then return end

    for i, self in ipairs(swarm) do
        if (self._exord_leader == nil) or not self._exord_leader._exord_is_leader then
            self._exord_leader = new_leader
        end
    end
    exord_swarm.promote_to_leader(new_leader)
    return new_leader
end

function exord_swarm.is_valid_leader(self)
    if not self then return false end
    if not self._exord_is_leader then return false end
    if self._hp <= 0 then return false end
    return true
end

function exord_swarm.get_leader(self)
    if not exord_swarm.is_valid_leader(self._exord_leader) then
        self._exord_leader = nil
    end

    if (self._get_leader_cooldown or 0) > 0 then return self._exord_leader end
    self._get_leader_cooldown = 0.5
    local pos = self.object:get_pos()
    local nearby_objects = minetest.get_objects_in_area(pos - _leader_area, pos + _leader_area)
    local closest_to_target
    local closest_d2_to_target
    for i, object in ipairs(nearby_objects) do
        local ent = object and object:get_luaentity()
        if ent and exord_swarm.is_valid_leader(ent) and ent._pmb_target then
            local d2 = exord_core.dist2(object:get_pos(), ent._pmb_target:get_pos())
            if (not closest_d2_to_target) or (d2 < closest_d2_to_target) then
                closest_d2_to_target = d2
                closest_to_target = ent
            end
        end
    end
    self._exord_leader_offset = exord_guns.vec3_randrange(-2, 2)
    self._exord_leader_offset.y = 0
    if not closest_to_target then
        return exord_swarm.new_leader(pos)
    end
    return closest_to_target
end

function exord_swarm.get_leader_dir(self)
    self._exord_leader = exord_swarm.get_leader(self)
    local lpos = self._exord_leader and self._exord_leader.object:get_pos()
    if lpos then
        local pos = self.object:get_pos()
        lpos = lpos + self._exord_leader.object:get_velocity()
        lpos = lpos + self._exord_leader_offset
        local dir = vector.direction(pos, lpos)
        return dir
    else
        self._exord_leader = nil
    end
    return nil
end

function exord_swarm.propagate_path(self, radius)
    local pos = self.object:get_pos()
    local nearby_objects = minetest.get_objects_inside_radius(pos, radius)
    for i, object in ipairs(nearby_objects) do
        local ent = object and object:get_luaentity()
        if ent and ent._exord_allow_steal_path and ((not ent._path) or (#ent._path < 3))  then
            ent._path = table.copy(self._path)
        end
    end
end

function exord_swarm.push_away(self, dtime)
    local pos = self.object:get_pos()
    local vel = vector.new(0,0,0)
    local count = 0
    local nearby_objects = minetest.get_objects_inside_radius(pos, 1)
    for i, object in ipairs(nearby_objects) do
        local ent = object and object:get_luaentity()
        if ent and ent._exord_swarm and ent._hp > 0 then
            vel = vel + vector.direction(object:get_pos(), pos)
            count = count + 1
        end
    end
    if count ~= 0 then
        vel = vel / count
        self.object:add_velocity(vel * dtime)
    end
end

-- get the direction to the next point in a path to the target
-- recalculate if you run out of points or the target is far away
-- remove points from the path as you reach them
function exord_swarm.check_get_path_dir(self, target_pos, force)
    local pos = self.object:get_pos()
    if (self._time_since_los or 0) < 0.1 then
        local nvyaw = perlin_cost_add:get_3d(pos*4 + self._path_perlin_offset*0.5)
        local dir = vector.direction(pos, target_pos)
        dir = minetest.yaw_to_dir(minetest.dir_to_yaw(dir) + (nvyaw*2-1) * 1.2)
        return dir
    elseif (self._time_since_los or 0) < 5 and self._last_los_pos then
        return vector.direction(pos, self._last_los_pos)
    end
    local allow_update = force
    allow_update = allow_update or ((self._path_cooldown or 0) <= 0)
    local wants_path = (not self._path) or (#self._path < 1)
    if wants_path and not self._exord_is_leader then
        local ldir = exord_swarm.get_leader_dir(self)
        if ldir then
            -- exord_swarm.debug_particle(pos, "#0f0", 1, ldir*10, 2)
            return ldir
        end
    end
    wants_path = wants_path or (self._last_target_pos
        and exord_mobpath.dist2(self._last_target_pos, target_pos) > exord_mobpath.dist2(pos, target_pos)*0.9)
    allow_update = allow_update and wants_path
    if allow_update then
        self._last_target_pos = target_pos
        self._path = exord_mobpath.astar(
            pos, target_pos,
            setmetatable({path_perlin_offset = self._path_perlin_offset}, _options_meta)
        )
        -- exord_swarm.propagate_path(self, 10)
        -- for i, p in ipairs(self._path) do
        --     exord_swarm.debug_particle(p, "#f00", 1, UP*10, 2)
        -- end
        self._path_cooldown = 2
    end

    if self._path and (#self._path > 0) then
        local next_point_in_path = self._path[#self._path]
        local dir = vector.direction(pos, next_point_in_path)
        local d2 = exord_mobpath.dist2(pos, next_point_in_path)
        if d2 < 0.5 then
            table.remove(self._path, #self._path)
        end
        return dir
    end
end

function exord_swarm.do_path(self)
    local pos = self.object:get_pos()
    local next = self._exord_path and self._exord_path[1]
    if (not next) then
        self._exord_path = nil
        return nil
    end
    -- for i, ipos in ipairs(self._exord_path) do
    --     exord_mobpath.debug_particle(ipos, "#ff0", 0.2, UP*100, 2)
    -- end
    local dist = exord_mobpath.dist2(pos, next)
    if dist < 1 then
        table.remove(self._exord_path, 1)
        if #self._exord_path > 0 then
            next = self._exord_path[1]
        else
            self._exord_path = nil
            return nil
        end
    end
    return vector.direction(pos, next)
end

function exord_swarm.get_path_dir(self)
    local dir = exord_swarm.do_path(self)
    return dir
end

function exord_swarm.get_target(self)
    local pos = self.object:get_pos()
    if not pos then return end
    if exord_player.is_object_fake_player(self._pmb_target)
    and self._pmb_target:get_luaentity()._hp > 0 then
        return self._pmb_target
    end
    self._pmb_target = nil
    self._time_since_los = 0
    local nearby = minetest.get_objects_in_area(
        vector.offset(pos, -10, -5, -10),
        vector.offset(pos,  10,  5,  10)
    )
    local fplayers = exord_player.get_alive_fake_players()
    local closest_dist = 9999999999
    local closest_fplayer
    local dist = 0
    for i, fplayer in ipairs(fplayers) do
        local fpos = fplayer.object:get_pos()
        dist = fpos and exord_core.dist2(fpos, pos)
        if fpos and dist < closest_dist then
            closest_dist = dist
            closest_fplayer = fplayer
        end
    end
    if closest_fplayer then
        self._pmb_target = closest_fplayer.object
        return closest_fplayer.object
    end
    return nil
end
