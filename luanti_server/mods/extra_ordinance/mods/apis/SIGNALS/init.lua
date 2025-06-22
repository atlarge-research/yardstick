

SIGNALS = {}

local CANCEL = "_cancel"
local FREE = "_free"
---If there are signals that requested removal, remove them from the callback list.
---@param source table
---@param removelist table
---@return nil
function SIGNALS.check_remove(source, removelist)
    for i = #removelist, 1, -1 do
        table.remove(source, removelist[i])
    end
end

---Allows you to optionally make your own eventbus instead of using the global one.
---This is good if you only want to signal locally and don't need to allow external access.
---This copies the entire object, so uh, maybe don't make too many of these.
---It isn't OOP after all...
---@param insert_in_table table | nil
function SIGNALS.new(insert_in_table)
    local object = insert_in_table or {}
    object._ASIGNALS_REG = {}
    ---Listen to an event, return `"_cancel"` to cancel the rest of the callbacks.
    ---@param tag string
    ---@param callback function
    ---@return nil
    object.LISTEN = function(tag, callback)
        if object._ASIGNALS_REG[tag] == nil then object._ASIGNALS_REG[tag] = {} end
        table.insert(object._ASIGNALS_REG[tag], callback)
    end
    ---Signal an event, and cancel if returns `"_cancel"`, returning the same so this effect can be chained.
    ---Return `"_free"` to remove this callback from the list.
    ---@param tag string
    ---@return string | nil
    object.SIGNAL = function(tag, ...)
        tag = object._ASIGNALS_REG[tag]
        if not tag then return end
        local removals = {}
        for i, callback in ipairs(tag) do
            local val = callback(...)
            if val == nil then
                -- do nothing
            elseif val == CANCEL then
                return CANCEL
            elseif val == FREE then
                table.insert(removals, i)
            end
        end
        SIGNALS.check_remove(tag, removals)
    end
    ---Calls all listeners and gets their returns such that `false` forces false return, and no `true` return is false.
    ---If there is no tag set / no listeners, then it will return `nil`.
    ---@param tag string
    ---@return boolean | nil
    object.CONDITIONAL = function(tag, ...)
        tag = object._ASIGNALS_REG[tag]
        if not tag then return nil end
        local had_true = false
        local removals = {}
        for i, callback in ipairs(tag) do
            local val = callback(...)
            if val == true then
                had_true = true
            elseif val == false then
                had_true = false
                break
            elseif val == CANCEL then
                break
            elseif val == FREE then
                table.insert(removals, i)
            end
        end
        SIGNALS.check_remove(tag, removals)
        return had_true
    end
    return object
end

-- The globally accessible copy of the signal register for intenal use.
SIGNALS.global = SIGNALS.new()
LISTEN = SIGNALS.global.LISTEN
SIGNAL = SIGNALS.global.SIGNAL
CONDITIONAL = SIGNALS.global.CONDITIONAL
