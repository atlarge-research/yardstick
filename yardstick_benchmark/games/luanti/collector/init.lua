-- Yardstick collector mod for Luanti
-- Collects performance metrics and exports them in Prometheus format

local http = minetest.request_http_api()
local metric_endpoint = "http://localhost:9091/metrics"
local collection_interval = 1 -- seconds

local metrics = {
    tick_duration = 0,
    packet_count = 0,
    player_count = 0,
    last_tick_time = minetest.get_us_time()
}

-- Register global step for tick timing
minetest.register_globalstep(function(dtime)
    local current_time = minetest.get_us_time()
    metrics.tick_duration = (current_time - metrics.last_tick_time) / 1000000
    metrics.last_tick_time = current_time
end)

-- Register packet counters
minetest.register_on_modchannel_message(function(channel, sender, message)
    metrics.packet_count = metrics.packet_count + 1
end)

-- Update player count
minetest.register_on_joinplayer(function(player)
    metrics.player_count = metrics.player_count + 1
end)

minetest.register_on_leaveplayer(function(player)
    metrics.player_count = metrics.player_count - 1
end)

-- Export metrics to Prometheus format
local function export_metrics()
    local metrics_text = string.format([[
# HELP luanti_tick_duration_seconds Server tick duration
# TYPE luanti_tick_duration_seconds gauge
luanti_tick_duration_seconds %f
# HELP luanti_packet_total Total packets processed
# TYPE luanti_packet_total counter
luanti_packet_total %d
# HELP luanti_player_count Current player count
# TYPE luanti_player_count gauge
luanti_player_count %d
]], metrics.tick_duration, metrics.packet_count, metrics.player_count)
    
    -- Write to file for Prometheus textfile collector
    local f = io.open("/var/lib/node_exporter/luanti_metrics.prom", "w")
    if f then
        f:write(metrics_text)
        f:close()
    end
end

-- Export metrics every second
minetest.register_globalstep(function(dtime)
    export_metrics()
end)

-- Log startup
minetest.log("info", "Yardstick collector mod loaded")

-- Track outgoing packets
local old_send = core.send_chat_message
if old_send then
    core.send_chat_message = function(message)
        metrics.packet_count = metrics.packet_count + 1
        return old_send(message)
    end
end

-- Send metrics to Prometheus endpoint
function send_metrics()
    -- Format metrics for Prometheus
    local payload = string.format([[
luanti_tick_duration_seconds %f
luanti_packet_total %d
luanti_player_count %d
    ]], 
    metrics.tick_duration,
    metrics.packet_count,
    metrics.player_count)
    
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

-- Export metrics every second
minetest.register_globalstep(function(dtime)
    send_metrics()
end) 