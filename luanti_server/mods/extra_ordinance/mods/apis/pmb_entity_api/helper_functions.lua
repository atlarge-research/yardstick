
function pmb_entity_api.on_activate(self, staticdata, dtime_s)
    local data = minetest.deserialize(staticdata)
    if minetest.get_modpath("pmb_mob_spawn") ~= nil and self.name then pmb_mob_spawn.add_to_cap(self.name) end
    if data then
        for key, val in pairs(data) do
            if key then
                self[key] = val
            end
        end
    else
        -- minetest.chat_send_all(dump(data))
    end
end

function pmb_entity_api.on_deactivate(self, removed)
    -- if minetest.get_modpath("pmb_mob_spawn") and self.name then pmb_mob_spawn.take_from_cap(self.name) end
end

function pmb_entity_api.get_staticdata(self)
    local data = {}
    if self._pmb_staticdata_load_list ~= nil then
        for i, key in pairs(self._pmb_staticdata_load_list) do
            if key then
                if minetest.is_player(self[key]) or (type(self[key]) == "table" and self[key].object) then
                    error("NO, YOU CANNOT SERIALIZE AN OBJECT!!! from: " .. key) end
                data[key] = self[key]
            end
        end
    end
    data._itemstring = self._itemstring
    data._flags = self._flags
    data._age = self._age
    return minetest.serialize(data)
end


function pmb_entity_api.move_toward_target(self, speed, do_vertical)
    if not self._pmb_target then return false end
    local dir = vector.direction(self.object:get_pos(), self._pmb_target:get_pos())
    local vel = self.object:get_velocity()
    if not do_vertical then dir.y = 0 end
    vel = vector.add(vector.multiply(vel, 0.95), vector.multiply(dir * speed, 0.05))
    self.object:set_velocity(vel)
end

function pmb_entity_api.object_is_mob(object)
    if object == nil then return false end
    local ent = object:get_luaentity()
    if ent and (ent._pmb_is_mob or ent._pmb_staticdata_load_list) then return object:get_luaentity() end
    return false
end

local function shortAngleDist(a0, a1)
    local max = math.pi * 2
    local da = (a1 - a0) % max
    return 2 * da % max - da
end

local function angleLerp(a0, a1, t)
    return a0 + shortAngleDist(a0, a1) * t
end

local function dir_to_pitch(dir)
    ---@diagnostic disable-next-line: deprecated
    return math.atan2(dir.y, math.sqrt(dir.x * dir.x + dir.z * dir.z))
end

local function dir_to_yaw(dir)
---@diagnostic disable-next-line: deprecated
    return -math.atan2(dir.x, dir.z)-- + math.pi * 0.5
end

local function dir_to_rotation(dir)
    return vector.new(
        dir_to_pitch(dir),
        dir_to_yaw(dir),
        0
    )
end

function pmb_entity_api.rotate_to_pos(self, to_pos, amount, do_vertical)
    local pos = self.object:get_pos()
    local dir = vector.direction(pos, to_pos)
    local from_rot = self.object:get_rotation()
    local to_rot = dir_to_rotation(dir)

    if amount ~= 1 then
        to_rot.y = angleLerp(from_rot.y, to_rot.y, amount)
    end
    if do_vertical then
        to_rot.x = angleLerp(from_rot.x, to_rot.x, amount)
    else
        to_rot.x = from_rot.x
    end

    self.object:set_rotation(to_rot)
end

function pmb_entity_api.rotate_to_target(self, amount, do_vertical)
    if not self._pmb_target then return false end
    local pos = self.object:get_pos()
    local tpos = self._pmb_target:get_pos()
    if not tpos then return false end
    pmb_entity_api.rotate_to_pos(self, tpos, amount, do_vertical)
end

function pmb_entity_api.path_reachable(self)
    local pos = self.object:get_pos()
    if self._pmb_path and #self._pmb_path > 0 and self._pmb_path[1].y > pos.y + 2  then
        return false
    end
    return true
end

function pmb_entity_api.rotate_to_path(self, amount)
    local tpos
    if self._pmb_path then tpos = self._pmb_path[1]
    elseif self._pmb_to_pos then tpos = self._pmb_to_pos end
    if not tpos then return false end

    local pos = self.object:get_pos()
    local dir = vector.direction(pos, tpos)
    local yaw = minetest.dir_to_yaw(dir)
    if amount ~= 1 then
        yaw = angleLerp(self.object:get_yaw(), yaw, amount)
    end
    self.object:set_yaw(yaw)
end

function pmb_entity_api.decelerate(self, amount, y_amount)
    local vel = self.object:get_velocity()
    vel.x = vel.x * amount
    vel.z = vel.z * amount
    if y_amount then vel.y = vel.y * y_amount end
    self.object:set_velocity(vel)
end

function pmb_entity_api.has_mobs_in_radius(pos, radius, names, min, max)
    local objects = minetest.get_objects_inside_radius(pos, radius)
    local count = 0
    for _, object in pairs(objects) do
        local mob = pmb_entity_api.object_is_mob(object)
        if mob then
            local has_name = true

            if names then
                has_name = false
                for i,name in pairs(names) do
                    if (name == mob.name) or (name == mob._name) then
                        has_name = true
                        break
                    end
                end
            end

            if has_name then
                count = count + 1
            end
            if count > max then return false end
        end
    end
    if count >= min then return true
    else return false end
end

function pmb_entity_api.alert_nearby(self, dist, filter)
    if not dist then dist = 30 end
    local nearby_objects = minetest.get_objects_inside_radius(self.object:get_pos(), dist)
    for _, object in pairs(nearby_objects) do
        local ent = object:get_luaentity()
        if ent and (not ent._pmb_target)
        and (filter and filter(ent) or ((not filter) and ent.name == self.name)) then
            ent._pmb_target = self._pmb_target
        end
    end
end

function pmb_entity_api.find_ground_at(pos, max_search)
    if not pos then return false end
    for i=0, max_search or 20 do
        local p = vector.offset(pos, 0, -i, 0)
        local def = minetest.registered_nodes[minetest.get_node(p).name]
        if def and def.walkable then
            return vector.offset(pos, 0, -i + 1, 0)
        end
    end
    return false
end

function pmb_entity_api.find_roam_target(self, distance)
    local target_pos = vector.offset(self.object:get_pos(), math.random()*distance, 5, math.random()*distance)
    local target = pmb_entity_api.find_ground_at(target_pos)
    if not target then return false end
    self._pmb_to_pos = target
    pmb_entity_api.get_path(self)
end

function pmb_entity_api.find_encircle(self, target, angle, dist)
    if not target then return nil end
    local p = self.object:get_pos()
    local tp = target:get_pos()
    local yaw = minetest.dir_to_yaw(vector.direction(tp, p))
    yaw = yaw + angle
    local dir = minetest.yaw_to_dir(yaw)
    local targetpos = pmb_entity_api.find_ground_at(tp + dir * dist)
    if not targetpos then return nil end
    self._pmb_to_pos = targetpos
    pmb_entity_api.get_path(self)
end

function pmb_entity_api.safe_get_pos(self)
    if not self then return end
    if minetest.is_player(self) then return self:get_pos() end
    return self.object:get_pos()
end

function pmb_entity_api.get_target_dist(self, offset)
    if not self._pmb_target then return false end
    local p = self.object:get_pos()
    local tp = self._pmb_target:get_pos()
    if offset then tp.y = tp.y + offset end
    if (not tp) or not p then return false end
    return (vector.distance(p, tp))
end

function pmb_entity_api.check_jump(self, strength, flags)
    if not flags then flags = {} end
    if self._pmb_jump_cooldown == nil then
        self._pmb_jump_cooldown = 0
    elseif self._pmb_jump_cooldown > 0 then
        return false
    end

    local pos = self.object:get_pos()
    local floor = vector.offset(pos, 0, -0.6, 0)
    local def = minetest.registered_nodes[minetest.get_node(floor).name]
    if not (def and def.walkable) then return false end
    -- local dir = vector.multiply(minetest.yaw_to_dir(self.object:get_yaw()), 0.7)
    local dir = self.object:get_velocity()
    dir.y = 0
    dir = vector.multiply(dir, flags.look_ahead_multiplier or 0.4)
    local look_dir = vector.multiply(minetest.yaw_to_dir(self.object:get_yaw()), 0.7)
    dir = vector.add(look_dir, dir)

    local in_front = vector.add(pos, dir)
    local in_front_above = vector.add(pos, vector.offset(dir, 0, 1, 0))
    in_front = minetest.registered_nodes[minetest.get_node(in_front).name]
    in_front_above = minetest.registered_nodes[minetest.get_node(in_front_above).name]
    if in_front and in_front.walkable and ((not in_front_above) or (not in_front_above.walkable)) then
        local vel = self.object:get_velocity()
        vel.y = strength
        self.object:set_velocity(vel)
        self._pmb_jump_cooldown = 1
    end
end

function pmb_entity_api.get_is_moving(self, horiz)
    local v = self.object:get_velocity()
    if math.floor(v.x) == 0 and (horiz or math.floor(v.y) == 0) and math.floor(v.z) == 0 then
        self._pmb_is_moving = true
        return true
    end
    self._pmb_is_moving = false
    return false
end

function pmb_entity_api.follow_target(self)
    pmb_entity_api.get_path(self, pmb_entity_api.min_cost)
    pmb_entity_api.do_path(self)
end

function pmb_entity_api.get_objects_of_type(position, distance, object_list)
    local ret_list = {}
    for _, object in ipairs(minetest.get_objects_inside_radius(position, distance)) do
        local luaent = object:get_luaentity()
        if luaent and luaent.name and (object_list[luaent.name] ~= nil) then
            ret_list[#ret_list+1] = object
        end
    end
    return ret_list
end

function pmb_entity_api.float_in_liquids(self, power, flags)
    if not flags then flags = {} end
    local pos = self.object:get_pos()
    if flags.offset then
        pos = vector.add(pos, flags.offset)
    end

    local cur_node = minetest.get_node(pos)
    local below_node = minetest.get_node(vector.offset(pos, 0, -0.3, 0))
    local in_water = (minetest.get_item_group(cur_node.name, "liquid") ~= 0)
    local above_water = (minetest.get_item_group(below_node.name, "liquid") ~= 0)
    if not in_water and not above_water then return end

    local vel = self.object:get_velocity()

    if in_water then
        vel = vector.multiply(vel, flags.damping or 0.8)
        vel.y = vel.y + (power)
        self.object:set_velocity(vel)
        return true
    elseif above_water then
        vel = vector.multiply(vel, flags.damping or 0.8)
        self.object:set_velocity(vel)
        return true
    end
end

function pmb_entity_api.apply_gravity(self, dtime, flags)
    if not flags then flags = {} end
    local gravity = 9.8
    if self._pmb_gravity then gravity = self._pmb_gravity end

    local last_vel = self.object:get_velocity()
    if not last_vel then return end
    self.object:set_velocity(vector.offset(last_vel, 0, -gravity * dtime, 0))
end

function pmb_entity_api.run_from(self, from_pos, flag)
    if flag == nil then flag = {} end
    if not self._pmb_to_pos then
        local pos = self.object:get_pos()
        local dir = vector.normalize(vector.subtract(from_pos, pos))
        local yaw = minetest.dir_to_yaw(dir)
        if flag.angle_deviation then
            yaw = yaw + (math.random()*2-1) * flag.angle_deviation
        end
        if flag.angle then
            yaw = yaw + flag.angle
        end
        pos = vector.add(pos, vector.multiply(dir, -(flag.distance or 20)))

        local ground = pmb_entity_api.find_ground_at(pos, 10) or pos

        local node = minetest.get_node(ground)
        if (not flag.allow_liquids) and (minetest.get_item_group(node.name, "liquid") ~= 0) then
            pos = vector.add(pos, vector.multiply(dir, (flag.distance or 20)))
            ground = pmb_entity_api.find_ground_at(pos, 10) or pos
        end

        self._pmb_to_pos = ground or pos
    end

    if self._pmb_to_pos then
        -- minetest.log(self._pmb_to_pos and "flee" or "no pos")
        pmb_entity_api.get_path(self, pmb_entity_api.min_cost)
        pmb_entity_api.do_path(self)
    end
end

function pmb_entity_api.get_and_follow_target(self, velocity_factor, flags)
    if not flags then flags = {} end
    if not velocity_factor then velocity_factor = 0 end

    if (not self._pmb_target) or (not self._pmb_target:get_pos()) then
        pmb_entity_api.get_target(self)
        if not self._pmb_target then return end
    end

    local tpos = self._pmb_target:get_pos()
    local refresh = flags.force_update or false
    if (not refresh) and (self._pmb_to_pos and math.random() < (flags.chance_to_refresh or 0.02)
    and vector.distance(tpos, self._pmb_to_pos) > (flags.distance_to_refresh or 3)) then
        refresh = true
    end

    if self._pmb_target and (tpos ~= nil) and refresh or (not self._pmb_to_pos) then
        -- anticipate movement
        if velocity_factor > 0 then
            local target_vel
            if minetest.is_player(self._pmb_target) then
                target_vel = self._pmb_target:get_velocity()
            else
                target_vel = self._pmb_target:get_velocity()
            end

            target_vel = vector.multiply((target_vel or vector.new(0,0,0)), velocity_factor)
            self._pmb_to_pos = vector.add(tpos, target_vel)

            self._pmb_path = {self._pmb_to_pos}
            -- minetest.log(minetest.colorize("#f00", "path set to {self._pmb_to_pos}"))
        -- don't anticipate movement
        else
            self._pmb_to_pos = tpos
        end
    end

    if flags.no_do_path then return end
    pmb_entity_api.follow_target(self)
end

function pmb_entity_api.punch_in_radius(self, interval, radius, flag)
    if self._pmb_since_attack <= (interval) then return false end
    if flag == nil then flag = {} end
    local pos = self.object:get_pos()
    for i, object in pairs(minetest.get_objects_inside_radius(pos, radius)) do
        if pmb_entity_api.is_valid_target(self, object, (flag.targets or self._pmb_hostile), flag.get_all) then
            object:punch(self.object, 1.0, {
                full_punch_interval = 1.0,
                damage_groups = flag.damage_groups or self._pmb_damage_groups or {
                    pierce=1,
                    slash=1,
                    blunt=1,
                }
            }, nil)
            self._pmb_since_attack = 0
        end
    end
end

-- simulates collisions
function pmb_entity_api.push_objects_in_radius(self, dtime, radius, amount)
    local pos = self.object:get_pos()
    for i, object in pairs(minetest.get_objects_inside_radius(pos, radius)) do repeat
        local tp = object:get_pos()
        if not tp then break end
        local dir = vector.direction(pos, tp)
        local is_player = minetest.is_player(object)

        if is_player and (object:get_meta():get_string("dead") == "true") then
            break
        elseif (not is_player) and not pmb_entity_api.object_is_mob(object) then
            break
        end

        if is_player then
            object:add_velocity(dir * (dtime * 20 * amount))
        else
            object:add_velocity(dir * (dtime * amount))
        end
        self.object:add_velocity(dir * (-dtime * amount))
    until true end
end

-- tells if has line of sight to some object, incl assumed eye height
function pmb_entity_api.has_los_to_object(self, object, force)

    -- only trigger sometimes because this is expensive
    self.__since_los = (self.__since_los or 0) + 1
    if (not force) and self.__since_los < 100 then
        return self._has_los_to_target
    else
        self.__since_los = 0
    end

    if not object then return false end
    local ent = object:get_luaentity()

    local op = object:get_pos()
    local p = self.object:get_pos()
    if (not p) or (not op) then return false end
    local eye_pos = 1.7
    if ent and ent._eye_height then eye_pos = ent._eye_height end
    if minetest.is_player(object) then eye_pos = object:get_properties().eye_height + object:get_eye_offset().y * 2 end

    op = vector.offset(op, 0, eye_pos, 0)
    p = vector.offset(p, 0, self._eye_height or 0.9, 0)

    self._has_los_to_target = false
    local ray = minetest.raycast(p, op, false, false)
    for pointed_thing in ray do
        if pointed_thing.type == "node" then
            local ndef = minetest.registered_nodes[minetest.get_node(pointed_thing.under).name]
            if ndef and ndef.walkable then
                self._has_los_to_target = false
                return false
            end
        end
    end

    self._has_los_to_target = true
    return self._has_los_to_target
end

-- return_only makes this not apply the damage but only return how far was fallen
function pmb_entity_api.test_fall_damage(self, dtime, return_only)
    local vel = self.object:get_velocity()
    local pos = self.object:get_pos()
    if vel.y < -dtime * 0.1 then -- is falling
        if not self._is_falling then
            self._is_falling = true
            self._fall_y = pos.y
        end
        self._last_fall_vel_y = vel.y
    else -- not falling
        if self._is_falling then -- not falling now but it was before
            if self._last_fall_vel_y < -dtime * 5 then
                local falldist = math.abs(self._fall_y - pos.y)
                if return_only then
                    return falldist
                elseif falldist >= 4 then
                    local damage_groups = { fall = (falldist-3) * 1 }
                    if not self.object:get_armor_groups().fall then
                        damage_groups = { blunt = (falldist-3) * 1 }
                    end
                    self.object:punch(self.object, 1, {
                        full_punch_interval = 1.0,
                        damage_groups = damage_groups
                    }, nil)
                end
            end
            self._is_falling = false
        end
        return
    end
end

local has_aom_fluidapi = (minetest.get_modpath("aom_fluidapi") ~= nil)
function pmb_entity_api.push_by_liquid(self, dtime, amount)
    if not has_aom_fluidapi then return end
    aom_fluidapi.push_by_liquid(self.object, dtime, amount)
end

function pmb_entity_api.get_current_animation_length(self)
    return ((self._animations[self._animation] or {}).speed or 24)
end
