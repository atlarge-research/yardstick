local elemname = "bform_listring"

---@class bform_listring : bform_prototype
---@field inventory string
---@field invlist string
local class = setmetatable({}, {__index = exord_bform.prototype})
class.type = elemname

-- listring[<inventory location>;<list name>]

---@return table
function class:render(fs, data, ...)
    table.insert(fs, "listring["..self.inventory..";"..self.invlist.."]")
    return fs
end

---@return bform_listring
function class.new(inventory, invlist)
    local ret = {
        inventory = inventory or "",
        invlist = invlist or "main",
        --
        children = {},
    }
    return setmetatable(ret, {__index = class})
end

exord_bform.element.listring = class
