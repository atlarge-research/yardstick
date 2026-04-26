# Yardstick Mineflayer workload runner.
#
# A thin Node.js base image with mineflayer and supporting libraries
# preinstalled. Workload .js files are bind-mounted into
# /opt/workload/scripts at runtime -- nothing is baked into the image -- so
# the image only needs to be republished when the npm dependencies change,
# not when the workload itself does. Any workload that requires only the
# bundled npm packages can be run from this image.
#
# Build and publish (the published image lives at
# docker.io/jdonkervliet/yardstick-mineflayer):
#
#   docker build -t jdonkervliet/yardstick-mineflayer:1.0 \
#       yardstick_benchmark/games/minecraft/workload
#   docker push jdonkervliet/yardstick-mineflayer:1.0
#
# At runtime, point the container at the entry script via apptainer's
# CMD-override: e.g. `apptainer instance run ... <image> <instance>` will
# default to the CMD set below; override per-workload by passing a
# different script path.

FROM node:22-alpine

WORKDIR /opt/workload

RUN npm install --omit=dev --omit=optional \
      mineflayer@^4.30.0 \
      mineflayer-pathfinder@^2.4.5 \
      rcon-client@^4.2.4

# /opt/workload/scripts is created by the bind-mount at runtime; the
# image just needs node_modules at /opt/workload/node_modules so that
# Node's module resolution walks up from /opt/workload/scripts/*.js and
# finds them.
WORKDIR /opt/workload/scripts

ENTRYPOINT ["node"]
