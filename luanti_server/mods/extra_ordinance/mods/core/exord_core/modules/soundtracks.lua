
exord_core.sfx = {}

exord_core.sfx._playing_tags = {}

local _sounds = {}
local class = {}
exord_core.sfx.__meta = {__index = class}

local function remove(self)
    local i = table.indexof(_sounds, self)
    if i > 0 then
        table.remove(_sounds, i)
    end
end

function class:remove()
    self.removed = true
end

function class:play_for_player(player)
    local def = table.copy(self.def.sound)
    def.to_player = player:get_player_name()
    def.gain = self.fade_in_time == nil and self.gain or 0.0001
    self.pl[player] = minetest.sound_play(self.name, def)
    if self.fade_in_time then
        local fade_per_sec = self.gain / self.def.fade_in_time
        minetest.sound_fade(self.pl[player], fade_per_sec, self.gain)
    end
    core.log("action", "PLAYING ".. self.name .. " with gain " .. self.gain)
end

function class:check_playing_for_player(player)
    if not self.pl[player] then
        self:play_for_player(player)
    end
end

function class:on_step(dtime)
    if self.fading then
        self.t_fade = (self.t_fade or 0) + dtime
        if self.t_fade > self.def.fade_out_time then
            self:remove()
        end
    end
    self.t_tick = (self.t_tick or 1) + dtime
    if self.t_tick > 1 then
        self.t_tick = self.t_tick - 1
        for i, player in ipairs(minetest.get_connected_players()) do
            self:check_playing_for_player(player)
        end
    end
    if self.removed then
        remove(self)
    end
end

function class:stop(no_fade)
    if no_fade then
        minetest.sound_stop(self.id)
    end
    local fade_per_sec = self.def.fade_out_time and (self.gain / self.def.fade_out_time) or 10
    self:remove()
    for player, id in pairs(self.pl) do
        core.log("action", "FADING ".. self.name .. id)
        minetest.sound_fade(id, fade_per_sec, 0)
    end
end

---- API

function exord_core.sfx.stop_tag(tag, no_fade)
    local self = exord_core.sfx._playing_tags[tag]
    if not self then return end
    core.log("action", "STOPPING TAG ".. tag)
    self:stop(no_fade)
    exord_core.sfx._playing_tags[tag] = nil
end

function exord_core.sfx.new(def)
    local self = setmetatable({}, exord_core.sfx.__meta)
    self.def = def
    self.name = def.name
    self.gain = def.gain
    self.pl = {}
    table.insert(_sounds, self)
    return self
end

function exord_core.sfx.start_track(tag, def, force)
    core.log("action", "STARTING TAG ".. tag)
    local already_playing = exord_core.sfx._playing_tags[tag]
    if already_playing and not force then return end
    if already_playing then
        exord_core.sfx.stop_tag(tag)
    end

    local self = exord_core.sfx.new(def)
    exord_core.sfx._playing_tags[tag] = self
end

minetest.register_globalstep(function(dtime)
    for i, sound in ipairs(_sounds) do
        sound:on_step(dtime)
    end
end)

--#TODO: implement fade in

exord_core.sfx.start_track("bgdrone", {
    name = "exord_ambient_rumble",
    gain = 0.4,
    fade_in_time = 6,
    fade_out_time = 1,
    sound = {
        loop = true,
    },
}, nil)

exord_core.sfx.start_track("bgfan", {
    name = "exord_fan_low",
    gain = 0.2,
    fade_in_time = 6,
    fade_out_time = 1,
    sound = {
        loop = true,
    },
}, nil)
