# Build the Minecraft tick collector that Telegraf's execd input runs.
#
# The compiled binary is committed to the repository: Telegraf runs it inside
# an unmodified upstream container, so it has to be staged onto the node as a
# self-contained file rather than built there. Rebuild and commit it whenever
# jolokia_get_minecraft_tick.go or the Go dependencies change.
#
#   make build    rebuild the committed binary (do this, then commit it)
#   make check    compile without touching the committed binary (used by CI)
#   make clean
#
# CGO is disabled and the binary is stripped so the result is a small static
# executable that runs in any container, independent of the host's libc.
#
# Note that the bytes are not reproducible across Go releases: a rebuild on a
# different toolchain produces a different -- equally valid -- binary. That's
# why CI only checks that the source still compiles.

BINARY := jolokia_get_minecraft_tick
SOURCE := jolokia_get_minecraft_tick.go
BUILD := CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -trimpath -ldflags="-s -w"

.PHONY: build check clean

build:
	$(BUILD) -o $(BINARY) $(SOURCE)

check:
	$(BUILD) -o $(shell mktemp -d)/$(BINARY) $(SOURCE)

clean:
	rm -f $(BINARY)
