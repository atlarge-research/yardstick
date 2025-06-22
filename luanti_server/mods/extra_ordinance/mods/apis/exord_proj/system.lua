
exord_proj._instances = {}

exord_proj.projectile_proto = {
    acceleration = vector.new(0, -2, 0),
    removed = false,
}

local is_debug = false

function exord_proj.dist2(p1, p2)
    return (p1.x - p2.x)^2 + (p1.z - p2.z)^2 + (p1.y - p2.y)^2
end

function exord_proj.projectile_proto.new(pos, obj)
    local self = setmetatable((obj and table.copy(obj)) or {}, {__index = exord_proj.projectile_proto})
    table.insert(exord_proj._instances, self)
    self:set_position(pos)
    self:set_velocity(vector.new(0,0,0))
    self.origin = vector.copy(pos)
    self.inaccuracy = 1
    self.speed = 100
    self.parent = nil
    self.damage_nodes = 1
    self.damage_players = 5
    self.max_range = 100
    return self
end



function exord_proj.projectile_proto:set_acceleration(acc) self.acceleration = vector.copy(acc) end
function exord_proj.projectile_proto:get_acceleration() return vector.copy(self.acceleration) end

function exord_proj.projectile_proto:set_velocity(vel) self.velocity = vector.copy(vel) end
function exord_proj.projectile_proto:get_velocity() return vector.copy(self.velocity) end

function exord_proj.projectile_proto:set_position(pos) self.position = vector.copy(pos) end
function exord_proj.projectile_proto:get_position() return vector.copy(self.position) end

function exord_proj.projectile_proto:remove() self.removed = true end


function exord_proj.projectile_proto:_can_collide(pointed_thing)
    if self.can_collide then
        return self:can_collide(pointed_thing)
    else return true end
end

function exord_proj.projectile_proto:_on_collide(pointed_thing)
    if self.on_collide then
        return self:on_collide(pointed_thing)
    else return true end
end


function exord_proj.projectile_proto:_on_step(dtime)
    if self.removed then return end
    if not self.last_pos then self.last_pos = self:get_position() end

    self.time = (self.time or 0) + dtime
    local dist2 = exord_proj.dist2(self.position, self.origin)

    if self.time > 10 or (dist2 > self.max_range ^ 2) then
        if self.on_removed then
            self.on_removed(self)
        end
        self:remove()
        return
    end

    if self.on_step then
        self:on_step(dtime)
        if self.removed then return end
    end

    local p = self:get_position()
    local v = self:get_velocity()
    local a = self:get_acceleration()

    v.x = v.x + a.x * dtime
    v.y = v.y + a.y * dtime
    v.z = v.z + a.z * dtime

    p.x = p.x + v.x * dtime
    p.y = p.y + v.y * dtime
    p.z = p.z + v.z * dtime

    self:set_position(p)
    self:set_velocity(v)

    -- debug
    if is_debug then
        local y = 0
        minetest.add_particle({
            pos = vector.offset(p, 0, 0, y),
            velocity = v*0.01,
            texture = "trf_nodes_outline.png",
            expirationtime = 5,
        })
        minetest.add_particle({
            pos = vector.offset(self.last_pos, 0, 0.1, y),
            velocity = v*0.01,
            texture = "trf_nodes_outline.png^[multiply:#f0f",
            expirationtime = 5,
        })
    end

    -- raycasts
    local dir = vector.direction(self.last_pos, p)
    local ray = minetest.raycast(self.last_pos, p, true, true)
    for pointed_thing in ray do
        -- by default always collides with everything
        if self:_can_collide(pointed_thing) then
            if self:_on_collide(pointed_thing) then
                self:remove()
                -- minetest.log("hit something")
                return -- stop if it collided and will not pierce
            end
        end
    end

    self.last_pos = self:get_position()
end



minetest.register_globalstep(function(dtime)
    for i = #exord_proj._instances, 1, -1 do
        local self = exord_proj._instances[i]
        self:_on_step(dtime)
        if self.removed then
            table.remove(exord_proj._instances, i)
        end
    end
end)

