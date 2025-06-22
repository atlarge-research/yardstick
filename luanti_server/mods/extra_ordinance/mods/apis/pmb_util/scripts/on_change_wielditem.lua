

function pmb_util.register_on_wield(param)
    minetest.override_item(param.name, {
        on_select = function(wieldstack, player)
            return param.on_change_to_item and param.on_change_to_item(player, wieldstack) or nil
        end,
        on_deselect = function(wieldstack, player)
            return param.on_change_from_item and param.on_change_from_item(player, wieldstack) or nil
        end,
        on_step = function(wieldstack, player, dtime)
            return param.on_step and param.on_step(player, dtime, wieldstack) or nil
        end,
    })
end


local wield_use_delay_pl = {}
function pmb_util.register_wield_use_delay(item_name, def)
    pmb_util.register_on_wield({
        name = item_name,
        on_change_from_item = function(player, wieldstack)
            wieldstack:get_meta():set_string("a", "")
            return wieldstack
        end,
        on_change_to_item = function(player, wieldstack)
            wieldstack:get_meta():set_string("a", "")
            return wieldstack
        end,
        on_step = function(player, dtime, wieldstack)
            local ct = player_info and player_info.get(player)
            if not ct then error("need player_info mod") return nil end
            local changes_made = false

            if ct.ctrl.place then
                local ret = pmb_util.try_rightclick(wieldstack, player, nil, true)
                if ret then
                    return ret
                end
            end

            if ct.just_pressed.place then
                wield_use_delay_pl[player] = {}
                wield_use_delay_pl[player].last_t = 99
                wield_use_delay_pl[player].total_time = 0
            elseif ct.just_released.place then
                wieldstack:get_meta():set_string("a", "")
                changes_made = true
            end
            if ct.ctrl.place and wield_use_delay_pl[player] then
                wield_use_delay_pl[player].total_time = (wield_use_delay_pl[player].total_time or 0) + dtime
                local t = math.ceil(wield_use_delay_pl[player].total_time * 4 * (def.sound_per_sec or 4))
                local last_t = (wield_use_delay_pl[player] and wield_use_delay_pl[player].last_t) or 0
                if def.sound and t ~= last_t and t % 2 == 0 then
                    local soundspec = table.copy(def.sound)
                    soundspec.object = player
                    minetest.sound_play(soundspec.name, soundspec, true)
                    wieldstack:get_meta():set_string("a", tostring(math.random(100)))
                    changes_made = true
                end

                wield_use_delay_pl[player].last_t = t

                if wield_use_delay_pl[player].total_time > def.windup then
                    wield_use_delay_pl[player] = nil
                    wieldstack:get_meta():set_string("a", "")
                    wieldstack = def.on_use(wieldstack, player, nil) or wieldstack
                    changes_made = true
                end
            end
            if changes_made then
                return wieldstack
            end
        end,
    })
end
