package main

import (
	"github.com/dragonfireclient/mt"
	"os"
	"sync"
)

func main() {
	toSrv := os.Args[1] == "ToSrvPkt"

	pkt, err := mt.DeserializePkt(os.Stdin, !toSrv)
	if err != nil {
		os.Stderr.WriteString(err.Error())
		os.Exit(1)
	}

	var wg sync.WaitGroup
	mt.SerializePkt(*pkt, os.Stdout, toSrv, &wg)
	wg.Wait()
}
