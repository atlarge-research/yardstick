

function exord_core.update_objectives_hud(player)
    local objectives_remaining = exord_core.objectives_max - exord_core.objectives_completed
    local obj_text = " "
    if exord_core.show_gametime and objectives_remaining > 0 then
        obj_text = exord_core.show_gametime and minetest.colorize("#aaaaaaa0", (objectives_remaining) .. " objectives remaining") or " "
    end
    if objectives_remaining > 0 then
        if pmb_hud.has_hud(player, "exord_core:objectives") then
            pmb_hud.change_hud(player, "exord_core:objectives", {
                text = obj_text,
            })
        else
            pmb_hud.add_hud(player, "exord_core:objectives", {
                type = "text",
                text = obj_text,
                position = {x=0.5, y=0.05},
                alignment = {x=0, y=1},
                z_index = 805,
                size = {x=1.8, y=0},
                offset = {x=0, y=80}
            })
        end
    elseif pmb_hud.has_hud(player, "exord_core:objectives") then
        pmb_hud.remove_hud(player, "exord_core:objectives")
    end
end


function exord_core.update_capture_hud(player)
    local time = math.floor(exord_core.objective_time_complete - exord_core.objective_time)
    local has_hud = time >= 0 and time ~= exord_core.objective_time_complete
    has_hud = has_hud and (exord_core.show_gametime)
    if (not has_hud) then
        if pmb_hud.has_hud(player, "exord_core:capture") then
            pmb_hud.remove_hud(player, "exord_core:capture")
            pmb_hud.remove_hud(player, "exord_core:return_to_obj")
            pmb_hud.remove_hud(player, "exord_core:time")
        end
        return
    end

    local f = 1 - time / exord_core.objective_time_complete
    local w = 200
    local fill = "blank.png"
    local cap_color = "#3be140d0"
    local uncap_color = "#2b9a9e60"
    local text_color = "#3be140d0"
    local objective = exord_core.current_objective
    if objective and not objective._is_ready then
        cap_color = "#ef4a4ad0"
        uncap_color = "#b31a1a80"
        text_color = "#b31a1ab0"

        pmb_hud.add_hud(player, "exord_core:return_to_obj", {
            type = "text",
            text = minetest.colorize("#f75b5b", "RETURN TO CAPTURE THE OBJECTIVE!"),
            position = {x=0.5, y=0.05},
            alignment = {x=0, y=1},
            z_index = 805,
            size = {x=2.0, y=0},
            offset = {x=0, y=100}
        })
    else
        pmb_hud.remove_hud(player, "exord_core:return_to_obj")
    end
    if f > 0 then
        fill = table.concat({
            "[fill:200x200:0,0:", uncap_color,
            "^[fill:", math.ceil(w*f), "x200:0,0:", cap_color
        })
    end

    local radial_image = fill .. "^[mask:exord_hud_capture.png"
    local time_text = minetest.colorize(text_color, time)
    if pmb_hud.has_hud(player, "exord_core:capture") then
        pmb_hud.change_hud(player, "exord_core:capture", {
            text = radial_image,
        })
        pmb_hud.change_hud(player, "exord_core:time", {
            text = time_text,
        })
    else
        pmb_hud.add_hud(player, "exord_core:capture", {
            type = "image",
            text = radial_image,
            position = {x=0.5, y=0.05},
            alignment = {x=0, y=0},
            z_index = 809,
            scale = {x = 0.5, y = 0.5},
            offset = {x = 0, y = 30 - 4},
        })
        pmb_hud.add_hud(player, "exord_core:time", {
            type = "text",
            text = time_text,
            position = {x=0.5, y=0.05},
            alignment = {x=0, y=1},
            z_index = 805,
            size = {x=3, y=0},
        })
    end
end
