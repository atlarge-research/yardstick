package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/gammazero/deque"
)

const PERIOD = 1000 * time.Millisecond

type JolokiaResponse struct {
	Value     []int64 `json:"value"`
	Status    int     `json:"status"`
	Timestamp int64   `json:"timestamp"`
}

type Tick struct {
	Duration  time.Duration
	StartTime time.Time
}

func getTickDurations(old, new []int64) []int64 {
	if new == nil || len(new) != 100 {
		panic("new must be length 100")
	}
	if old == nil {
		return []int64{}
	}
	if len(old) != 100 {
		panic("old must be length 100")
	}

	var indicesFirstNew []int
	var indicesLastNew []int

	for i := range 100 {
		j := (i + 1) % 100
		if old[i] == new[i] && old[j] != new[j] {
			indicesFirstNew = append(indicesFirstNew, j)
		}
		if old[i] != new[i] && old[j] == new[j] {
			indicesLastNew = append(indicesLastNew, i)
		}
	}

	// new == old, perhaps the server is paused.
	if len(indicesFirstNew) == 0 || len(indicesLastNew) == 0 {
		return []int64{}
	}

	indexFirstNew := indicesFirstNew[0]
	indexLastNew := indicesLastNew[0]

	if len(indicesFirstNew) != 1 || len(indicesLastNew) != 1 {
		fmt.Println("RARE EVENT!")
		maxlen := 0
		for _, s := range indicesFirstNew {
			for _, e := range indicesLastNew {
				var d int
				if s <= e {
					d = e - s
				} else {
					d = 100 - s + e + 1
				}
				if d > maxlen {
					maxlen = d
					indexFirstNew = s
					indexLastNew = e
				}
			}
		}
	}

	if indexFirstNew <= indexLastNew {
		return new[indexFirstNew : indexLastNew+1]
	}

	return append(new[indexFirstNew:], new[:indexLastNew+1]...)
}

func getDuration(ticks []int64) time.Duration {
	duration := int64(0)
	for _, v := range ticks {
		duration += max(int64(50), v)
	}
	return time.Duration(duration)
}

func main() {
	data := map[string]string{
		"type":      "read",
		"mbean":     "net.minecraft.server:type=Server",
		"attribute": "tickTimes",
		"path":      "",
	}

	dataEnc, err := json.Marshal(data)
	if err != nil {
		panic(err)
	}

	client := &http.Client{}
	url := "http://localhost:8778/jolokia/"

	var prev []int64

	t := time.Now()

	tickNumber := 0
	loopIteration := 0
	var computedTimestamp time.Time
	var prevTickDuration int64

	var tickSlidingWindow deque.Deque[Tick]

	for {
		t = t.Add(PERIOD)
		time.Sleep(time.Until(t))

		req, err := http.NewRequest("POST", url, bytes.NewBuffer(dataEnc))
		if err != nil {
			panic(err)
		}
		req.Header.Set("Content-Type", "application/json")

		resp, err := client.Do(req)
		if err != nil {
			panic(err)
		}

		body, err := io.ReadAll(resp.Body)
		resp.Body.Close()
		if err != nil {
			panic(err)
		}

		var respObj JolokiaResponse
		err = json.Unmarshal(body, &respObj)
		if err != nil {
			panic(err)
		}
		curr := respObj.Value
		tickTimes := getTickDurations(prev, curr)
		duration := getDuration(tickTimes)
		prev = curr

		now := time.Now()
		// Compute the TPS and print it
		start := now.Add(-duration)
		for _, tickDuration := range tickTimes {
			tickSlidingWindow.PushBack(Tick{Duration: time.Duration(tickDuration), StartTime: start})
			start = start.Add(time.Duration(max(tickDuration, 50)))
		}
		for tickSlidingWindow.Len() > 0 && now.Sub(tickSlidingWindow.Front().StartTime) > 1*time.Second {
			tickSlidingWindow.PopFront()
		}
		tps := tickSlidingWindow.Len()
		fmt.Printf("minecraft_tick tps=%di %d\n", tps, now.UnixNano())

		// Compute the timestamp and duration of every tick and print it
		for _, tickDuration := range tickTimes {
			if computedTimestamp.IsZero() {
				computedTimestamp = now.Add(-duration)
			} else {
				// convert ns to ms for comparison
				prevMs := prevTickDuration / 1_000_000
				sleepMs := max(prevMs, 50)
				computedTimestamp = computedTimestamp.Add(time.Duration(sleepMs) * time.Millisecond)
			}

			fmt.Printf("minecraft_tick tick_duration_ms=%f,tick_number=%di,loop_iteration=%di,timestamp_ms=%di %d\n",
				float64(tickDuration)/1_000_000.0,
				tickNumber,
				loopIteration,
				now.UnixMilli(),
				computedTimestamp.UnixNano(),
			)

			// fmt.Println("measurement,tick_duration_ms,tick_number,loop_iteration,timestamp_ms,computed_timestamp_ms")
			// fmt.Printf(
			// 	"minecraft_tick_duration,%f,%d,%d,%d,%d\n",
			// 	float64(tickDuration)/1_000_000.0,
			// 	tickNumber,
			// 	loopIteration,
			// 	now.UnixMilli(),
			// 	computedTimestamp.UnixMilli(),
			// )

			tickNumber++
			prevTickDuration = tickDuration
		}

		loopIteration++
	}
}
