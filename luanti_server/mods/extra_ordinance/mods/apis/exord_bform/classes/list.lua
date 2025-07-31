local elemname = "bform_list"

---@class bform_list : bform_prototype
---@field inventory string
---@field listname string
---@field invsize table
---@field listspacing number
---@field startindex number
local class = setmetatable({}, {__index = exord_bform.prototype})
class.type = elemname

-- list[<inventory location>;<list name>;<X>,<Y>;<W>,<H>;<starting item index>]

---@return table
function class:render(fs, data, ...)
    table.insert(fs, "style_type[list;spacing="..(self.listspacing or 0)..";size=0.9]")
    table.insert(fs, "list["..self.inventory..";"..self.listname..";")
    table.insert(fs, self.pos[1]..","..self.pos[2]..";")
    table.insert(fs, self.invsize[1]..","..self.invsize[2]..";")
    table.insert(fs, (self.startindex or 1) .. "]")
    table.insert(fs, "container["..self.pos[1]..","..self.pos[2].."]")
    return fs
end

---@return table
function class:render_after(fs, data, ...)
    table.insert(fs, "container_end[]")
    return fs
end

---@return bform_list
---@param inventory string
---@param listname string
---@param offset table
---@param invsize table
---@param listspacing number
---@param startindex number
---@param id string
function class.new(inventory, listname, offset, invsize, listspacing, startindex, id)
    local ret = {
        id = id,
        inventory = inventory,
        listname = listname,
        offset = offset or {0, 0},
        size = {
            invsize[1] * (1 + listspacing),
            invsize[2] * (1 + listspacing),
        },
        invsize = invsize,
        startindex = startindex,
        listspacing = listspacing,
        --
        pos = {0, 0},
        children = {},
    }
    return setmetatable(ret, {__index = class})
end

exord_bform.element.list = class
