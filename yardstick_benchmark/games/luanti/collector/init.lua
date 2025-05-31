-- Yardstick collector mod for Luanti
local http = minetest.request_http_api()
local metric_endpoint = "http://localhost:9091/metrics"
local collection_interval = 1 -- seconds

-- Metrics
local metrics = {
    tick_duration = 0,
    player_count = 0,
    packets_in = 0,
    packets_out = 0,
    last_timestamp = os.time()
}

-- Track tick duration
minetest.register_globalstep(function(dtime)
    metrics.tick_duration = dtime
    metrics.player_count = #minetest.get_connected_players()
    
    -- Only send metrics once per second
    local current_time = os.time()
    if current_time - metrics.last_timestamp >= collection_interval then
        send_metrics()
        metrics.last_timestamp = current_time
    end
end)

-- Track network packets
minetest.register_on_modchannel_message(function(channel_name, sender, message)
    metrics.packets_in = metrics.packets_in + 1
end)

-- Send metrics to Prometheus endpoint
function send_metrics()
    -- Format metrics for Prometheus
    local payload = string.format([[
luanti_tick_duration_seconds %f
luanti_player_count %d
luanti_packet_in_total %d
luanti_packet_out_total %d
    ]], 
    metrics.tick_duration,
    metrics.player_count,
    metrics.packets_in,
    metrics.packets_out)
    
    -- Send metrics via HTTP
    if http then
        http.fetch({
            url = metric_endpoint,
            method = "POST",
            data = payload,
            timeout = 1,
        }, function(res) end)
    end
    
    -- Also log metrics to server log for backup
    minetest.log("action", "[Yardstick] " .. payload)
end

-- Track outgoing packets
local old_send = core.send_chat_message
if old_send then
    core.send_chat_message = function(message)
        metrics.packets_out = metrics.packets_out + 1
        return old_send(message)
    end
end

-- Track player connections
minetest.register_on_joinplayer(function(player)
    minetest.log("action", "[Yardstick] Player joined: " .. player:get_player_name())
end)

minetest.register_on_leaveplayer(function(player)
    minetest.log("action", "[Yardstick] Player left: " .. player:get_player_name())
end)

minetest.log("action", "Yardstick collector mod initialized") 