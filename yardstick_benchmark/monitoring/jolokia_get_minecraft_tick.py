#!/usr/bin/env python3

from urllib import request
import json
import time

PERIOD_S = 2.5

def get_tick_durations(old, new):
    assert old is None or len(old) == 100
    assert len(new) == 100

    if old is None:
        return []

    indices_first_new = []
    indices_last_new = []

    for i in range(100):
        j = (i + 1) % 100
        if old[i] == new[i] and old[j] != new[j]:
            indices_first_new.append(j)
        if old[i] != new[i] and old[j] == new[j]:
            indices_last_new.append(i)

    index_first_new = indices_first_new[0]
    index_last_new = indices_last_new[0]

    if len(indices_first_new) != 1 or len(indices_last_new) != 1:
        print("RARE EVENT!")
        maxlen = 0
        for s in indices_first_new:
            for e in indices_last_new:
                d = 0
                if s <= e:
                    d = e - s
                else:
                    d = 100 - s + e + 1
                if d > maxlen:
                    maxlen = d
                    index_first_new = s
                    index_last_new = e


    if index_first_new <= index_last_new:
        return new[index_first_new:index_last_new+1]
    else:
        return new[index_first_new:] + new[:index_last_new+1]


if __name__ == "__main__":
    print("measurement,tick_duration_ms,tick_number,loop_iteration,timestamp_ms,computed_timestamp_ms")

    data_dict = {"type": "read", "mbean": "net.minecraft.server:type=Server", "attribute": "tickTimes", "path": ""}
    data_enc = json.dumps(data_dict).encode('utf-8')
    r = request.Request("http://localhost:8778/jolokia/", data=data_enc)

    prev = None

    t = time.monotonic()

    tick_number = 0
    loop_iteration = 0
    computed_timestamp = None
    prev_tick_duration = None

    while True:
        t += PERIOD_S
        now = time.monotonic()
        time.sleep(t - now)
        with request.urlopen(r) as resp:
            resp_enc = resp.read()
            # 'b{"request":{"mbean":"net.minecraft.server:type=Server","attribute":"tickTimes","type":"read"},"value":[289409,204240,209490,200170,214170,213459,200270,214330,433520,637339,630230,384160,446700,228030,557510,257059,618959,956190,603250,208380,242239,561869,319440,262310,220520,241469,499589,377190,361880,276440,215829,205450,214360,197440,585350,308020,302799,393030,256400,253980,257850,240670,398650,222530,365240,218000,207360,293930,596580,452230,621069,395489,218000,216990,218930,620510,419869,205880,218020,662480,683600,598459,262660,202140,282060,222220,204070,200060,230420,249950,227590,237730,232170,527770,642410,671939,550010,210690,217470,203400,233720,238790,213600,204250,283690,255309,225790,517470,437730,320380,340419,220750,207610,214930,598840,310579,228690,257850,205210,217100],"status":200,"timestamp":1717945225}'
            resp_dict = json.loads(resp_enc.decode('utf-8'))
            curr = resp_dict["value"]
            tick_times = get_tick_durations(prev, curr)
            prev = curr

            for tick_duration in tick_times:
                if computed_timestamp is None:
                    computed_timestamp = now
                else:
                    computed_timestamp += max(50, prev_tick_duration)
                print(f"minecraft_tick_duration,{tick_duration/1000000},{tick_number},{loop_iteration},{now*1000},{computed_timestamp}")
                tick_number += 1
                prev_tick_duration = tick_duration
        loop_iteration += 1
