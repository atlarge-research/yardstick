
-- Multiple Finite State Machine
MFSM = {}

local _state_machine_globalsteps = {}

-- runs every time you change stuff, to make sure your entity is set up correctly
function MFSM.init_states(self)
    if self._MFSM_has_init then return end
    self._MFSM_active_states = {}
    self._MFSM_state_meta = {}
    self._MFSM_state_map = {}
    self._MFSM_states = self._MFSM_states or {}
    for i, state in ipairs(self._MFSM_states) do
        self._MFSM_state_map[state.name] = state
    end
    self._MFSM_has_init = true
end
-- get the temporary metadata that is given to each state seperately
---@param state_name string
function MFSM.get_state_meta(self, state_name)
    local meta = self._MFSM_state_meta[state_name]
    if not meta then meta = {}; self._MFSM_state_meta[state_name] = meta end
    return meta
end
-- do the state code, based on functype e.g. on_step or on_end
---@param state_name string
---@param functype string
function MFSM.do_state(self, state_name, functype, ...)
    if self._MFSM_state_map[state_name] and self._MFSM_state_map[state_name][functype] then
        self._MFSM_state_map[state_name][functype](self, ...)
    end
end
-- set a single state and trigger its on_start if it isn't already active
---@param state_name string
---@param active boolean | nil
---@param exclusive boolean | nil
function MFSM.set_state(self, state_name, active, exclusive)
    MFSM.init_states(self)
    -- drop other states if flag set
    if exclusive then
        MFSM.reset_all_states(self, {state_name=true})
    end
    local has_state = self._MFSM_active_states[state_name]
    active = (active==true) -- convert to only bool
    local meta = MFSM.get_state_meta(self, state_name)
    if has_state and not active then
        MFSM.do_state(self, state_name, "on_end", meta)
        self._MFSM_state_meta[state_name] = nil
        self._MFSM_active_states[state_name] = active
    elseif active and not has_state then
        MFSM.do_state(self, state_name, "on_start", meta)
        self._MFSM_state_meta[state_name] = {
            state_time = 0
        }
        self._MFSM_active_states[state_name] = active
    end
end
-- set a map of states to their given values
---@param states table
---@param exclusive boolean | nil
function MFSM.set_states(self, states, exclusive)
    MFSM.init_states(self)
    -- drop other states if flag set
    if exclusive then
        MFSM.reset_all_states(self, states)
    end
    -- set all states to their respective values
    for state_name, val in pairs(states) do
        MFSM.set_state(self, state_name, val, false)
    end
end
-- put this in your on_step of your entity (or use the enable_globalstep if it's not an entity)
function MFSM.on_step(self, dtime)
    MFSM.init_states(self)
    for i, state in ipairs(self._MFSM_states) do
        if self._MFSM_active_states[state.name] then
            local meta = MFSM.get_state_meta(self, state.name)
            MFSM.do_state(self, state.name, "on_step", dtime, meta)
            meta.state_time = meta.state_time + dtime
        end
    end
end
-- removes all active states
---@param exclude_list table | nil
function MFSM.reset_all_states(self, exclude_list)
    if not exclude_list then exclude_list = {} end
    for state_name, is_active in pairs(self._MFSM_active_states) do
        local state = self._MFSM_state_map[state_name] or {}
        if (is_active == true) and (exclude_list[state_name] == nil)
        and not state.is_protected then
            MFSM.set_state(self, state_name, false)
        end
    end
end
-- add to the globalstep list so that `on_step` happens automatically
function MFSM.enable_globalstep(self)
    if self._globalstep_enabled then return end
    self._globalstep_enabled = true
    table.insert(_state_machine_globalsteps, self)
end
-- remove from the globalstep list so it doesn't `on_step`
function MFSM.disable_globalstep(self)
    if not self._globalstep_enabled then return end
    local i = table.indexof(_state_machine_globalsteps, self)
    if i > 0 then
        table.remove(_state_machine_globalsteps, i)
    end
end

minetest.register_globalstep(function(dtime)
    -- iterate backwards in case any state machine removes itself
    for i = #_state_machine_globalsteps, 1, -1 do
        _state_machine_globalsteps[i]:on_step(dtime)
    end
end)

MFSM.__meta = {__index = MFSM}

-- create a new state machine, optionally inserting it into `host` table
---@param host table
---@return table
function MFSM.new(host)
    return setmetatable(host or {}, MFSM.__meta)
end
