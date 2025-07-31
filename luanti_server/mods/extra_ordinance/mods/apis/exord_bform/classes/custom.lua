local elemname = "bform_custom"

local class = setmetatable({}, {__index = exord_bform.prototype})
class.type = elemname

function class:render(fs, data, ...)
    if self.callback_before then
        self.callback_before(self, fs, data, ...)
    end
    table.insert(fs, table.concat(self.static_elements))
    return fs
end

---@return table
function class:render_after(fs, data, ...)
    if self.callback_after then
        self.callback_after(self, fs, data, ...)
    end
    return fs
end

function class.new(size, id, static_elements_list, callback_before, callback_after)
    local ret = {
        id = id,
        offset = {0, 0},
        size = size or {0, 0},
        static_elements = static_elements_list or {},
        children = {},
        spacing = {0,0},
        callback_before = callback_before,
        callback_after = callback_after,
    }
    return setmetatable(ret, {__index = class})
end

exord_bform.element.custom = class
