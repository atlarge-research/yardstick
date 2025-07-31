


function pmb_entity_api.do_drops(self)
    if not self._drop then return nil end
    local pos = self.object:get_pos()
    if not pos then return nil end
    local drops = self._drop.items
    local max = self._drop.max_items
    local c = 0 -- counter for items
    for _, drop in pairs(drops) do
        if drop.chance == 1 or math.random() * (drop.rarity or 1) <= 1 then
            for i, item in pairs(drop.items) do
                local p = vector.offset(pos, math.random()-0.5, math.random() * 0.3+0.2, math.random()-0.5)
                minetest.add_item(p, ItemStack(item))
                c = c + 1
                if c >= max then
                    return true
                end
            end
        end
    end
end
