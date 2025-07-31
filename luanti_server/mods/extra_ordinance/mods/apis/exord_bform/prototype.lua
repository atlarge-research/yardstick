

---@class bform_prototype
---@field children table
---@field parent bform_prototype
---@field on_fields function
---@field ignore_not_on_enter boolean
---@field ignore_spacing boolean
---@field _reg_on_changed table
---@field _reg_on_fields table
---@field id_reg table
---@field id string
---@field extent table
---@field spacing table
---@field space_evenly boolean
---@field expand boolean
---@field visible boolean
---@field fill table
---@field padding table
---@field dir table
---@field offset table
---@field size table
---@field pos table
---@field type string
exord_bform.prototype = {}
exord_bform.prototype.type = "bform_prototype"
exord_bform.prototype.visible = true
function exord_bform.prototype.render_children(self, fs, data, ...)
    for i, child in ipairs(self.children) do
        if child.visible then
            child:render(fs, data, ...)
            child:render_children(fs, data, ...)
        end
        if child.visible and child.render_after then
            child:render_after(fs, data, ...)
        end
    end
    return fs
end

---@return bform | bform_prototype
function exord_bform.prototype.get_root(self)
    local node = self
    local iter = 0
    while node.parent ~= nil and iter < 1000 do
        node = node.parent
        iter = iter + 1
    end
    return node
end

function exord_bform.prototype.on_fields(self, player, formname, fields)
end

---@return self
function exord_bform.prototype._propagate_event(self, player, formname, fields)
    if self._reg_on_fields then
        for i, callback in ipairs(self._reg_on_fields) do
            callback(self, player, formname, fields)
        end
    end
    if (fields[self.id] ~= nil) and self.on_fields then
        if (not self.ignore_not_on_enter) or fields.key_enter_field == self.id then
            self:on_fields(player, formname, fields)
        end
    end
    for i, child in ipairs(self.children) do
        exord_bform.prototype._propagate_event(child, player, formname, fields)
    end
    return self
end

exord_bform.changed_forms = {}

---@param self bform | bform_prototype
---@return nil
function exord_bform.prototype._on_changed(self, source)
    if not exord_bform.changed_forms[self] then
        exord_bform.changed_forms[self] = {}
    end
    self.changes_acknowledged = false
    table.insert(exord_bform.changed_forms[self], source.id or "no id")
end

minetest.register_globalstep(function(dtime)
    ---@param form bform
    for form, sources in pairs(exord_bform.changed_forms) do
        if sources then
            form.id_reg = {}
            form:init_children()
            exord_bform.changed_forms[form] = false
            if form.on_changed then
                form:on_changed(sources or {})
            end
            if form._reg_on_changed then
                for i, callback in ipairs(form._reg_on_changed) do
                    callback(form, sources)
                end
            end
        end
    end
end)

---@return nil
function exord_bform.prototype.register_on_changed(self, callback)
    local root = self:get_root()
    if root and (root ~= self) then
        root:register_on_changed(callback)
        return -- don't reg on branches, only root
    end

    if self._reg_on_changed == nil then self._reg_on_changed = {} end
    table.insert(self._reg_on_changed, callback)
end

---@return nil
function exord_bform.prototype.register_on_fields(self, callback)
    local root = self:get_root()
    if root and (root ~= self) then
        root:register_on_fields(callback)
        return -- don't reg on branches, only root
    end

    if self._reg_on_fields == nil then self._reg_on_fields = {} end
    table.insert(self._reg_on_fields, callback)
end

---@return nil
function exord_bform.prototype.signal_changes(self)
    local root = exord_bform.prototype.get_root(self)
    exord_bform.prototype._on_changed(root, self)
end

---@return nil
function exord_bform.prototype.init_child(self, child)
    child.parent = self
    if child.id and (child.id ~= "") then
        local root = self:get_root()
        exord_bform.debug(child.id .. " is inside " .. (child.parent.id or "nil") .. " and root is " .. (root.id or "nil"))
        if root.id_reg == nil then root.id_reg = {} end
        root.id_reg[child.id] = child
    end
    child:init_children(self)
end

---@return nil
function exord_bform.prototype.init_children(self)
    for i, child in ipairs(self.children or {}) do
        self:init_child(child)
    end
    return self
end

table.indexof = table.indexof or function(list, val)
    for k, v in pairs(list) do
        if v == val then return k end
    end
end

---@param self bform_prototype
---@param element bform_prototype
---@return bform_prototype
function exord_bform.prototype.remove_child(self, element)
    local i = table.indexof(self.children, element)
    if i > 0 then
        element.parent = nil
        table.remove(self.children, i)
        exord_bform.prototype.signal_changes(self)
    end
    return element
end

---@param self bform_prototype
---@param id string
---@param replacement bform_prototype
---@return bform_prototype | nil
function exord_bform.prototype.replace_id(self, id, replacement)
    local removal = self:get_element_by_id(id)
    if not removal then return end
    local parent = removal.parent
    if not parent then return end
    parent:remove_child(removal)
    replacement:set_id(id)
    parent:add_child(replacement)
    return replacement
end

---@param self bform_prototype
---@param element bform_prototype
---@return bform_prototype
function exord_bform.prototype.add_child(self, element)
    if element.parent then -- don't allow being contained by multiple
        exord_bform.prototype.remove_child(element.parent, element)
    end
    element.parent = self
    table.insert(self.children, element)
    exord_bform.prototype.signal_changes(self)
    return element
end

---@param self bform_prototype
---@param children table
---@return self
function exord_bform.prototype.add_children(self, children)
    for i, child in ipairs(children or {}) do
        self:add_child(child)
    end
    exord_bform.prototype.signal_changes(self)
    return self
end

---@param self bform_prototype
---@param id string
---@return bform_prototype | nil
function exord_bform.prototype.get_element_by_id(self, id)
    local root = exord_bform.prototype.get_root(self)
    if root.id_reg == nil then root.id_reg = {} end
    return root.id_reg[id]
end

-- calculate extend of this node by its max extending element
---@return nil
function exord_bform.prototype.compare_extent(self, v2)
    for i = 1, 2 do
        if v2[i] > self.extent[i] then self.extent[i] = v2[i] end
    end
end

---@param self bform_prototype
---@return nil
function exord_bform.prototype.apply_offsets(self)
    local pos = {0,0}
    self.dir = self.dir or {0,1}
    local dir = {math.abs(self.dir[1]), math.abs(self.dir[2])}
    -- local dir = {self.dir[1], self.dir[2]} -- too much work to allow negatives
    self.extent = self.extent or {0,0}
    self.extent[1] = 0
    self.extent[2] = 0

    local count = 0
    local last_spacer_child
    if self.space_evenly then
        for _, child in ipairs(self.children) do
            local is_flow = not (child.fill or child.ignore_spacing or child.absolute_pos)
            if (is_flow) then
                count = count + 1
                last_spacer_child = child
                exord_bform.prototype.apply_offsets(child)
            end
        end
    end

    if self.fill then
        if not self.size then self.size = {0,0} end
        local px = (self.parent and self.parent.size) or self.size or {0,0}
        self.size[1] = math.max(px[1] + self.fill[1], self.size[1])
        self.size[2] = math.max(px[2] + self.fill[2], self.size[2])
        if not self.offset then self.offset = {0,0} end
        self.offset[1] = -self.fill[1]*0.5
        self.offset[2] = -self.fill[2]*0.5
    end
    if self.expand then
        if not self.size then self.size = {0,0} end
        local px = (self.parent and self.parent.size) or self.size or {0,0}
        self.size[1] = math.max(px[1] * (dir[1] or 0), self.size[1])
        self.size[2] = math.max(px[2] * (dir[2] or 0), self.size[2])

        if self.parent and self.parent.padding then
            self.size[1] = self.size[1] - self.parent.padding[1] * 2
            self.size[2] = self.size[2] - self.parent.padding[2] * 2
        end
    end

    local flowsize = self.size and {
        self.size[1],
        self.size[2],
    } or {0,0}
    local flowoffset = {0,0}

    if self.padding then
        flowsize[1] = flowsize[1] - self.padding[1] * 2
        flowsize[2] = flowsize[2] - self.padding[2] * 2
        flowoffset[1] = flowoffset[1] + self.padding[1]
        flowoffset[2] = flowoffset[2] + self.padding[2]
    end

    local last_space = (last_spacer_child and last_spacer_child.size) or {0,0}
    if last_spacer_child and last_spacer_child.extent then
        last_space[1] = math.max(last_space[1], last_spacer_child.extent[1])
        last_space[2] = math.max(last_space[2], last_spacer_child.extent[2])
    end

    if last_spacer_child then
        minetest.log(last_spacer_child.label or "none")
    end
    local space = {
        ((flowsize[1] - last_space[1]) / math.max(1, count-1)) * dir[1],
        ((flowsize[2] - last_space[2]) / math.max(1, count-1)) * dir[2],
    }

    if count == 1 then
        space[1] = ((flowsize[1])/2 - last_space[1]/2) * dir[1]
        space[2] = ((flowsize[2])/2 - last_space[2]/2) * dir[2]
    end

    local i = 0
    for _, child in ipairs(self.children) do repeat
        -- cascade down the tree
        child:apply_offsets()

        local is_flow = not (child.fill or child.ignore_spacing or child.absolute_pos)

        local spacing = child.extent or child.size or {0,0}
        if self.space_evenly and is_flow then
            if count == 1 then i = 1 end
            pos[1] = (i) * space[1] + flowoffset[1]
            pos[2] = (i) * space[2] + flowoffset[2]
            i = i + 1
        end

        if child.absolute_pos then
            child.pos[1] = child.absolute_pos[1]
            child.pos[2] = child.absolute_pos[2]
        elseif child.pos and is_flow then
            if not child.offset then child.offset = {0,0} end
            child.pos[1] = pos[1] + child.offset[1]
            child.pos[2] = pos[2] + child.offset[2]
        elseif child.pos and child.offset then
            child.pos[1] = child.offset[1]
            child.pos[2] = child.offset[2]
        end

        -- update offset pos
        if not self.space_evenly then
            pos[1] = pos[1] + spacing[1] * dir[1]
            pos[2] = pos[2] + spacing[2] * dir[2]
            i = i + 1
        end

        exord_bform.prototype.compare_extent(self, spacing)
    until true end

    if (not self.visible) or not self.ignore_spacing then
        exord_bform.prototype.compare_extent(self, pos)
        exord_bform.prototype.compare_extent(self, self.size or pos)
        if self.spacing then
            self.extent[1] = self.extent[1] + self.spacing[1]
            self.extent[2] = self.extent[2] + self.spacing[2]
        end
    elseif self.ignore_spacing then
        self.extent[1] = 0--self.size[1]
        self.extent[2] = 0--self.size[2]
    end
end

---@return self
function exord_bform.prototype.set_params(self, params)
    for k, v in pairs(params) do
        self[k] = v
    end
    exord_bform.prototype.signal_changes(self)
    return self
end

function exord_bform.prototype:_set_value(field, val)
    self[field] = val
    exord_bform.prototype.signal_changes(self)
    return self
end
-- Sets the bounds of the element, used by many things like images etc.
---@param value table
function exord_bform.prototype:set_size(value) return self:_set_value("size", value) end
-- Forces a position within the parent
---@param value table
function exord_bform.prototype:set_absolute_pos(value) return self:_set_value("absolute_pos", value) end
-- Flow direction. Negatives not implemented, probably ~= 1 will cause issues.
---@param value table
function exord_bform.prototype:set_dir(value) return self:_set_value("dir", value) end
-- ID that is gettable from the form.
---@param value string
function exord_bform.prototype:set_id(value) return self:_set_value("id", value) end
-- Pushes the element around without affecting any other.
---@param value table
function exord_bform.prototype:set_offset(value) return self:_set_value("offset", value) end
-- Adds to its extend by this much to space elements.
---@param value table
function exord_bform.prototype:set_spacing(value) return self:_set_value("spacing", value) end
-- When this element gets clicked etc, calls this function(player, formname, fields).
---@param value function
function exord_bform.prototype:set_on_fields(value) return self:_set_value("on_fields", value) end
-- If true, completely ignores own spacing, such that other elements' positions are not affected by it.
---@param value boolean
function exord_bform.prototype:set_ignore_spacing(value) return self:_set_value("ignore_spacing", value) end
-- Tries to place child elements evenly within the bounds of this element.
---@param value boolean
function exord_bform.prototype:set_space_evenly(value) return self:_set_value("space_evenly", value) end
-- Expands to fill only in the direction (dir) that this element flows.
---@param value boolean
function exord_bform.prototype:set_expand(value) return self:_set_value("expand", value) end
-- If an element is not visible, it is like it doesn't exist at all.
---@param value boolean
function exord_bform.prototype:set_visible(value) return self:_set_value("visible", value) end
-- Completely fills the parent container. Value determines extra overflow.
---@param value table
function exord_bform.prototype:set_fill(value) return self:_set_value("fill", value) end
-- Reduces internal space, so that elements come away from the edges this much on all sides.
---@param value table
function exord_bform.prototype:set_padding(value) return self:_set_value("padding", value) end
