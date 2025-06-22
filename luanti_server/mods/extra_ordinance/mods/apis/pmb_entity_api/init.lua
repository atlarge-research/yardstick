pmb_entity_api = {}

function pmb_entity_api.push_sorted(list, val, key)
    local val_key = key(val)
    if not list[1] then
        table.insert(list, val)
        return list
    end
    for ind, tval in list do
        if val_key < key(tval) then
            table.insert(list, ind, val)
            return list
        elseif vector.equals(val.pos, tval.pos) then
            return list
        end
    end
end

function pmb_entity_api.smooth_path(path)
    local ret_path = {}
    local last_pos = nil
    for _, pos in ipairs(path) do
        if not last_pos then
            table.insert(ret_path, pos)
        elseif last_pos.y ~= pos.y then
            table.insert(ret_path, last_pos)
            table.insert(ret_path, pos)
        end
        last_pos = pos
    end
    return ret_path
end


function pmb_entity_api.default_cost(pos1, pos2)
    local c = vector.distance(pos1, pos2)
    if minetest.get_item_group(minetest.get_node(pos2).name, "liquid") > 0 then
        c = c * 1.2
    end
    return c
end

-- Position format:
-- { pos = vector,
--   prev_pos = vector,
--   cost = float,
-- }

local function node_def(pos)
    return minetest.registered_nodes[(minetest.get_node(pos).name)] or {}
end

function pmb_entity_api.valid_node(nodepos, frompos)
    local offset = vector.subtract(nodepos, frompos)
    if offset.x == 0 and offset.z == 0 then
        return false
    end

    if node_def(nodepos).walkable then
        return false
    end
    if not node_def(vector.offset(nodepos, 0, -1, 0)).walkable then
        return false
    end
    if node_def(vector.offset(nodepos, 0, 1, 0)).walkable then
        return false
    end

    if offset.x ~= 0 and offset.z ~= 0 then
        if node_def(vector.offset(nodepos, -offset.x, 0, 0)).walkable then
            return false
        end
        if node_def(vector.offset(nodepos, 0, 0, -offset.z)).walkable then
            return false
        end
    end
    return true
end

function pmb_entity_api.astar(s_pos, e_pos, min_cost, max_tries, max_queue, valid_node, cost)
    -- minetest.log(minetest.colorize("#0f0", "astar"))
    if not max_tries then
        max_tries = 30
    end
    if not max_queue then
        max_queue = 1000
    end
    if not valid_node then
        valid_node = pmb_entity_api.valid_node
    end
    if not min_cost then
        function min_cost(pos1, pos2)
            return vector.distance(pos1, pos2)
        end
    end
    -- this will determine how much it should seek this terrain or avoid it
    cost = cost or pmb_entity_api.default_cost
    local stack = { { pos = s_pos,
        prev_pos = nil,
        cost = 0, } }

    local function total_cost(pos)
        return min_cost(pos.pos, e_pos) + pos.cost
    end

    local closest = stack[1]
    local c_key = min_cost(stack[1].pos, e_pos)
    local iters = 0

    while stack[1] and min_cost(stack[1].pos, e_pos) > 1 and iters < max_tries do
        -- minetest.log(dump(stack))
        local from = table.remove(stack, 1)
        local to_add = {}
        for dx = -1, 1 do
            for dy = -1, 1 do
                for dz = -1, 1 do
                    local nodepos = vector.offset(from.pos, dx, dy, dz)
                    if valid_node(nodepos, from.pos) then
                        table.insert(to_add,
                            { pos = nodepos, prev_pos = from, cost = from.cost + cost(from.pos, nodepos) })
                    end
                end
            end
        end
        for _, val in ipairs(to_add) do
            local val_key = total_cost(val)
            local val_mkey = min_cost(val.pos, e_pos)
            if val_mkey < c_key then
                closest = val
                c_key = val_mkey
            end
            if not stack[1] then
                table.insert(stack, val)
            else
                for ind, tval in ipairs(stack) do
                    if val_key < total_cost(tval) then
                        table.insert(stack, ind, val)
                        break
                    end
                end
            end
        end
        for i = max_queue, #stack do
            stack[i] = nil
        end
        iters = iters + 1
        --minetest.log(dump(stack))
    end

    local path = {}
    local last_node = closest
    while not vector.equals(last_node.pos, s_pos) do
        table.insert(path, 1, last_node.pos)
        last_node = last_node.prev_pos
    end

    return path
end

function pmb_entity_api.astar_smooth(s_pos, e_pos, max_tries, min_cost)
    return pmb_entity_api.smooth_path(pmb_entity_api.astar(s_pos, e_pos, max_tries, min_cost))
end

function pmb_entity_api.min_cost_2d(pos1, pos2)
    return math.sqrt(((pos1.x - pos2.x) ^ 2) + ((pos1.z - pos2.z) ^ 2))
end

function pmb_entity_api.min_cost(pos1, pos2)
    return vector.distance(pos1, pos2)
end


function pmb_entity_api.check_has_valid_target(self)
    if self._pmb_ignore_player_death then return end
    if not self._pmb_target then return end
    if minetest.is_player(self._pmb_target) then
        if self._pmb_target:get_meta():get_string("dead") == "true" then
            self._pmb_target = nil
        end
    end
end

function pmb_entity_api.is_valid_target(self, object, targets, get_all)
    if not targets then targets = self._pmb_hostile or {} end
    local ent = object:get_luaentity()
    if object ~= self.object and (object:is_player() and targets["player"]) or (
    ((ent and ent.name ~= "__builtin:item") and get_all) or (targets[ent.name] or targets[ent.name])) then
        -- don't pick players that are dead
        if object:is_player() and object:get_meta():get_string("dead") == "true" then return false end
        return true
    end
    return false
end

function pmb_entity_api.get_target(self, targets, flag, force)

    -- only trigger sometimes because this is expensive
    self.__since_target = (self.__since_target or 0) + 1
    if (not force) and self.__since_target < 50 then
        return
    else
        self.__since_target = 0
    end

    if not flag then flag = {} end
    local p = self.object:get_pos()

    if not targets then
        targets = self._pmb_hostile
    end

    if not self._pmb_range then
        self._pmb_range = 20
    end

    local tpos = (self._pmb_target and self._pmb_target:get_pos()) or nil

    if not self._pmb_target or (not tpos) or (vector.distance(tpos, p) > self._pmb_range) then
        self._pmb_target = nil
        for _, object in ipairs(minetest.get_objects_inside_radius(p, self._pmb_range)) do
            if pmb_entity_api.is_valid_target(self, object, targets) then
                if flag.no_los or pmb_entity_api.has_los_to_object(self, object, true) then
                    self._pmb_target = object
                    break
                end
            end
        end
    end
    if self._pmb_target and not flag.no_to_pos then
        self._pmb_to_pos = self._pmb_target:get_pos() or self._pmb_to_pos
        if self._pmb_path_timer and self._pmb_path_timer > 70 then
            self._pmb_path = nil
        end
    end
end

function pmb_entity_api.get_wander(self, freq)
    if not self._pmb_wander_timer then
        self._pmb_wander_timer = 0
    end
    self._pmb_wander_timer = self._pmb_wander_timer + 1
    if freq > self._pmb_wander_timer then return end

    local p = self.object:get_pos()

    if not self._pmb_range then
        self._pmb_range = 20
    end

    if not self._pmb_to_pos then
        local r = self._pmb_range
        local tpos = vector.new((math.random()*2-1)*r + p.x, p.y, (math.random()*2-1)*r + p.z)
        local dir = 1
        -- if in air, look down
        local tdef = minetest.registered_nodes[minetest.get_node(tpos).name]
        if tdef and not tdef.walkable then
            dir = -1
        end
        for i = 0, 20 do
            local ipos = vector.offset(tpos, 0, dir * i, 0)
            local idef = minetest.registered_nodes[minetest.get_node(ipos).name]
            local walkable = idef and idef.walkable
            if (dir == -1 and walkable) or (dir == 1 and not walkable) then
                tpos = ipos
                if dir == -1 then
                    tpos = vector.offset(ipos, 0, -dir, 0)
                end
                break
            end
        end
        if self._water_mob or minetest.get_item_group(minetest.get_node(tpos).name, "liquid") == 0 then
            self._pmb_to_pos = tpos
            self._pmb_path = {}
            self._pmb_wander_timer = 0
            pmb_entity_api.get_path(self, pmb_entity_api.min_cost)
        end
    end
end

function pmb_entity_api.do_path(self, speed, acceleration)
    local p = self.object:get_pos()
    acceleration = acceleration or 0.02

    if not speed then
        speed = self._pmb_speed
    end

    if not self._pmb_stuck_timer then
        self._pmb_stuck_timer = 0
    end

    if not self._pmb_last_pos then
        self._pmb_last_pos = p
    end

    if pmb_entity_api.min_cost_2d(self._pmb_last_pos, p) < 0.02 then
        self._pmb_stuck_timer = self._pmb_stuck_timer + 1
    else
        self._pmb_stuck_timer = 0
    end

    if self._pmb_stuck_timer > 70 then
        self._pmb_path = nil
        self._pmb_to_pos = nil
        self._pmb_stuck_timer = 0
    end

    if not self._pmb_last_pos then
        self._pmb_last_pos = p
    end

    local last_vel = self.object:get_velocity()

    if (not self._pmb_path) or #self._pmb_path == 0 then
        self._pmb_to_pos = nil
        return
    end
    if pmb_entity_api.min_cost_2d(p, self._pmb_path[1]) < 1.2 then
        table.remove(self._pmb_path, 1)
    end
    if #self._pmb_path == 0 then
        if self._floating then
            self.object:set_velocity(vector.new(0, 0, 0))
        else
            self.object:set_velocity(vector.new(0, last_vel.y, 0))
        end
        return
    end
    local next_pos = self._pmb_path[1]
    --minetest.log(dump(next_pos))
    local dir = vector.direction(p, next_pos)
    dir = vector.multiply(dir, speed)
    dir = vector.add(vector.multiply(last_vel, 1-acceleration), vector.multiply(dir, acceleration))
    if not self._floating then
        dir.y = last_vel.y
    end
    self.object:set_velocity(dir)
    -- self.object:set_velocity(vector.offset(vector.multiply(dir, speed), 0, last_vel.y, 0))


    self._pmb_last_pos = p
end

function pmb_entity_api.get_path(self, cost)
    local p = self.object:get_pos()
    if not self._pmb_path_timer then
        self._pmb_path_timer = 70
    end

    if ((not self._pmb_path) or #self._pmb_path == 0) and self._pmb_path_timer >= 70 then
        if self._pmb_to_pos then
            self._pmb_path = pmb_entity_api.astar(p, self._pmb_to_pos, cost, nil)
            self._pmb_path_timer = 0
            self._pmb_to_pos = self._pmb_path[1]
        end
    end
end

function pmb_entity_api.on_step(self, dtime, moveresult)
    -- time the jumps
    if not self._pmb_jump_cooldown then
        self._pmb_jump_cooldown = 0
    elseif self._pmb_jump_cooldown > 0 then
        self._pmb_jump_cooldown = self._pmb_jump_cooldown - 1
    end
    if not self._pmb_no_liquid_flow then
        pmb_entity_api.push_by_liquid(self, dtime, 2)
    end
    pmb_entity_api.check_has_valid_target(self)
end

function pmb_entity_api.set_state(self, state)
    self._pmb_state_time = 0
    if self._states[state].on_state_start then
        self._states[state].on_state_start(self)
    end
    self._state = state
    -- minetest.log(minetest.colorize("#f0f", state))
    pmb_entity_api.set_my_animation(self, self._states[self._state].animation)
end

function pmb_entity_api.mob_on_step(self, dtime, moveresult)
    local ss = os.clock()
    -- make sure all the timers are set
    if self._pmb_state_time == nil then self._pmb_state_time = 0
    else self._pmb_state_time = (self._pmb_state_time or 0) + dtime end
    if self._age == nil then self._age = 0
    else self._age = self._age + dtime end
    if self._pmb_since_attack == nil then self._pmb_since_attack = 0
    else self._pmb_since_attack = (self._pmb_since_attack or 0) + dtime end

    -- prevent having a target which is being destroyed by the engine
    local target_pos = self._pmb_target and self._pmb_target:get_pos()
    if not target_pos then self._pmb_target = nil end

    pmb_entity_api.on_step(self, dtime, moveresult)

    if not self._state then
        if self._default_state then
            pmb_entity_api.set_state(self, self._default_state)
        else
            pmb_entity_api.set_state(self, next(self._states))
        end
        if self._pmb_state_time == 0 then
            pmb_entity_api.set_my_animation(self, self._states[self._state].animation)
        end
    end

    if not self._pmb_path_timer then
        self._pmb_path_timer = 0
    end
    self._pmb_path_timer = self._pmb_path_timer + 1


    local new_state

    if self._states.on_step then
        new_state = self._states.on_step(self, dtime, moveresult)
    end
    if new_state ~= "die" and self._states[self._state].step then
        new_state = self._states[self._state].step(self, dtime, moveresult)
    end
    if new_state == "die" then return false end

    if new_state and self._states[new_state] then
        pmb_entity_api.set_state(self, new_state)
    end

    -- local last_vel = self.object:get_velocity()
    -- if self._pmb_gravity == nil then self._pmb_gravity = 9.8 end
    -- if not last_vel then return end
    -- self.object:set_velocity(vector.offset(last_vel, 0, -self._pmb_gravity * dtime, 0))
end

function pmb_entity_api.do_states()
    return pmb_entity_api.mob_on_step
end

function pmb_entity_api.set_my_animation(self, animation_name, overrides, from_blacklist)
    local object = self.object

    if not overrides then overrides = {} end

    -- don't allow or only allow some animations
    if from_blacklist and from_blacklist[self._animation] then return false end
    -- stop if the animation isn't defined

    local anim = self._animations[animation_name]
    if (not anim) then return false end
    if self._animation == animation_name then return false end

    -- keep track of the animation
    self._animation = animation_name

    if anim.mesh then
        object:set_properties({ mesh = anim.mesh })
    end
    if anim.textures then
        object:set_properties({ textures = anim.textures })
    end

    if overrides.mesh then
        object:set_properties({ mesh = overrides.mesh })
    end
    if overrides.textures then
        object:set_properties({ textures = overrides.textures })
    end

    if overrides.speed == nil then overrides.speed = anim.speed end
    if overrides.speed == nil then overrides.speed = 24 end

    if overrides.loop == nil then overrides.loop = anim.loop end
    if overrides.loop == nil then overrides.loop = true end

    object:set_animation(
        overrides.frames or anim.frames or { x = 0, y = 0 },
        overrides.speed,
        overrides.blend or anim.blend or 0,
        overrides.loop
    )
    return true
end


local mod_path = minetest.get_modpath(minetest.get_current_modname())

dofile(mod_path .. DIR_DELIM .. "helper_functions.lua")
dofile(mod_path .. DIR_DELIM .. "mob_drops.lua")
dofile(mod_path .. DIR_DELIM .. "damage" .. DIR_DELIM .. "damage.lua")
