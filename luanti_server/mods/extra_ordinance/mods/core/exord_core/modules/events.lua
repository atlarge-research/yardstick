

exord_core.running_events = {}
exord_core.registered_events = {}
exord_core.registered_events_list = {}

exord_core.Event = {
    event_time = 0,
}
exord_core.Event.__meta = {__index = exord_core.Event}


local function add(self)
    table.insert(exord_core.running_events, self)
end

local function remove(self)
    local i = table.indexof(exord_core.running_events, self)
    if i > 0 then
        exord_core.running_events[i] = nil
    end
end

function exord_core.Event:_on_step(dtime)
    if not self._init then
        self._init = true
        if self.on_start then
            self:on_start()
        end
    end
    self.event_time = self.event_time + dtime
    if self.on_step then
        self:on_step(dtime)
    end
    if self.removed then
        remove(self)
        if self.on_end then
            self:on_end()
        end
    end
end

function exord_core.Event:remove()
    self.removed = true
end


function exord_core.Event.new(def)
    local self = setmetatable({}, def.__meta)
    add(self)
    return self
end

function exord_core.event_on_step(dtime)
    for i, event in ipairs(exord_core.running_events) do
        event:_on_step(dtime)
    end
end

minetest.register_globalstep(exord_core.event_on_step)

function exord_core.register_event(name, def)
    def = setmetatable(def, exord_core.Event.__meta)
    def.name = name
    def.__meta = {__index = def}
    exord_core.registered_events[name] = def
    table.insert(exord_core.registered_events_list, def)
end

function exord_core.start_event(name)
    local def = exord_core.registered_events[name]
    if not def then return end
    return exord_core.Event.new(def)
end

function exord_core.get_running_events()
    return exord_core.running_events
end

function exord_core.event_request(event_list, meta, dtime)
    if meta.current_event and not meta.current_event.removed then
        return
    elseif meta.current_event and meta.current_event.removed then
        meta.time_to_next = meta.current_event.get_time_to_next_event and meta.current_event:get_time_to_next_event() or 3
        if ISDEBUG then meta.time_to_next = 5 end
        meta.current_event = nil
    end

    meta.time_to_next = (meta.time_to_next or 0) - dtime
    if meta.time_to_next <= 0 then
        -- core.log("looking for new event")
        for i = 1, 100 do
            local ri = math.random(1, #event_list)
            local event_name = event_list[ri]
            local event_def = exord_core.registered_events[event_name]
            if event_def then
                meta.current_event = exord_core.start_event(event_name)
                -- core.log("started new event")
                return
            else
                -- core.log("could not find event")
            end
        end
    end
end

exord_core.register_event("test", {
    on_step = function(self, dtime)
        core.log("test step")
        if self.event_time > 0.1 then
            self:remove()
        end
    end,
    on_start = function(self)
        core.log("test start")
    end,
    on_end = function(self)
        core.log("test end")
    end,
    get_time_to_next_event = function(self)
        return math.random(10, 20)
    end,
})

exord_core.register_event("mob_surge", {
    on_step = function(self, dtime)
        self.t = (self.t or 3) - dtime
        if self.t < 0 then
            self.t = self.t + 4
            exord_core.mobs_spawn_dist_min = 40
            exord_core.mobs_spawn_dist_max = 60
            exord_core.spawn_mobs(exord_core.difficulty * 30)
        end
        if self.event_time > 3.1 + 4 * 2 then
            self:remove()
        end
    end,
    on_start = function(self)
        -- exord_core.voiceover.play_voice_situation("mob_surge")
    end,
    on_end = function(self)
        SIGNAL("update_mobspawning_rules")
    end,
    get_time_to_next_event = function(self)
        return math.random(10, 30)
    end,
})

exord_core.register_event("mob_burrow", {
    on_step = function(self, dtime)
        self.t = (self.t or 3) - dtime
        if self.t < 0 then
            self.t = self.t + 1
            exord_core.mobs_spawn_dist_min = 12
            exord_core.mobs_spawn_dist_max = 20
            exord_core.spawn_mobs(exord_core.difficulty * 10)
        end
        if self.event_time > 3.1 + 3 then
            self:remove()
        end
    end,
    on_start = function(self)
        exord_swarm.burrow_time_min = exord_swarm.burrow_time_min * 2
        -- exord_core.voiceover.play_voice_situation("mob_burrow")
    end,
    on_end = function(self)
        exord_swarm.burrow_time_min = exord_swarm.burrow_time_min / 2
        SIGNAL("update_mobspawning_rules")
    end,
    get_time_to_next_event = function(self)
        return math.random(10, 30)
    end,
})

-- local meta = {}
-- minetest.register_globalstep(function(dtime)
--     exord_core.event_request({
--         "test",
--     }, meta, dtime)
-- end)
