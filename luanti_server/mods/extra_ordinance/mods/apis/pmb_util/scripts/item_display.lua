



local fs = table.concat({
"formspec_version[6]",
"size[24.00,12.0]",
"no_prepend[]",
"style_type[item_image_button;bgcolor=#fff;bgcolor_hovered=#fff;bgcolor_pressed=#fff]",
"style_type[item_image_button;textcolor=#8c3f5d;border=false]",
"style_type[item_image_button;bgimg=blank.png^[noalpha^[colorize:#f0f:255;bgimg_hovered=blank.png^[noalpha^[colorize:#f0f:255]",
"item_image_button[4,4;2,2;",
"__name__"..";notag".. ";]"})

-- shows a preview of a node or item, so that you can get reliable images of nodes
minetest.register_chatcommand("item_display", {
    params = "item_display [itemname]",
    description = "Shows an item as an inventory item",
    privs = {server = true},
    func = function(name, param)
        local spec = string.gsub(fs, "__name__", param)
        minetest.show_formspec(name, "item_display", spec)
    end
})

