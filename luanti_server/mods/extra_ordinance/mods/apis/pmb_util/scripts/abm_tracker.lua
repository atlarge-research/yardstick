
local abm_calls = {}
local do_abm_checks = true
local avg = 0

function pmb_util.did_abm(trace)
    if abm_calls[trace] == nil then
        abm_calls[trace] = 1
    else
        abm_calls[trace] = abm_calls[trace] + 1
    end
end

local output_next = false

function pmb_util.get_abm_calls()
    output_next = true
end

local timer = 5
minetest.register_globalstep(function(dtime)
    if timer > 0 then timer = timer - dtime return
    else timer = 5 end
    local total = 0
    for trace, callcount in pairs(abm_calls) do
        total = total + callcount
        if output_next then minetest.chat_send_all(trace.." : "..callcount) end
        abm_calls[trace] = 0
    end
    if output_next then output_next = false end
    avg = ((avg * 39) + total)/40
end)
