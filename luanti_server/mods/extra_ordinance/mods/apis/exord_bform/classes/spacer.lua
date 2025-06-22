local elemname = "bform_spacer"

---@class bform_spacer : bform_prototype
local class = setmetatable({}, {__index = exord_bform.prototype})
class.type = elemname

-- spacer[<X>,<Y>;<W>,<H>;<texture name>;<middle>]

---@return table
function class:render(fs, data, ...)
    return fs
end

---@return bform_spacer
function class.new(size, spacing, id)
    local ret = {
        id = id,
        size = size or {0, 0},
        offset = {0, 0},
        spacing = spacing or {0,0},
        --
        pos = {0, 0},
        children = {},
    }
    return setmetatable(ret, {__index = class})
end

exord_bform.element.spacer = class
