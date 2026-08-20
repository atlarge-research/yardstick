# Yardstick GUI

Desktop application for automating the Yardstick benchmark setup, experiment execution, and result visualization.

## Table of Contents

- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Scripts](#scripts)
- [Release Packaging](#release-packaging)
- [Development workflow](#development-workflow-without-electron)
- [To Do](#to-do)

## Architecture

The app has three layers: a **backend server**, a **frontend client**, and an **Electron shell** that bundles them into a desktop app.

```
gui/
  server/       Express + Socket.IO backend
  client/       React + Vite frontend
  electron/     Electron wrapper
```

### Server (`server/`)

An Express server (port 3001) that handles all remote operations. It exposes a Socket.IO namespace that the client connects to.

- **SSH** -- Uses the `ssh2` library to open persistent SSH sessions to remote hosts (DAS-5, DAS-6, AWS EC2, or any custom host). Supports password and private-key auth, and optional jump-host tunneling (ProxyJump) for off-campus access.
- **Local mode** -- Runs commands directly via Node's `child_process.spawn` for local-machine setups.
- **Pipeline** -- Orchestrates the full install pipeline (Miniconda, conda env, dependencies, workspace clone, verification) by executing each step over the active SSH or local session and streaming stdout/stderr back to the client in real time.
- **Experiments** -- Launches the Ansible-driven experiment workflow (provision, deploy, run, collect, clean) and streams output. (incomplete)
- **Results** -- Lists available experiment runs on the remote filesystem, reads their CSV metric files, parses them, and sends structured chart data back to the client. (incomplete)
- **Uninstall** -- Pipes `server/uninstall.sh` to the connected host to reverse the install pipeline (conda env, Miniconda, run directories, Docker artifacts, leftover processes). Options are passed as `YS_*` environment variables, so the same file also runs standalone with `--dry-run`, `--purge` and `--nvm` flags.

The server keeps no database -- all state lives in memory for the duration of a session.

### Client (`client/`)

A single-page React app built with Vite.

- **UI framework** -- Chakra UI for layout and styling, react-icons for icons, Recharts for charts.
- **Socket hook** -- `useYardstick` manages all Socket.IO communication, connection state, terminal output buffers, environment checks, and pipeline/experiment progress in one custom hook.
- **Pages** -- Tabs after connecting: Setup (environment detection + install pipeline), Experiment (configure and launch a benchmark run), Results (incomplete still), Cloud, Terminal (run arbitrary commands on the remote host), and Uninstall (preview and remove the installation).

The production build (`npx vite build`) outputs static files to `client/dist/`, which the Express server serves at `/`.

### Electron (`electron/`)

A thin wrapper that turns the web app into a native desktop window.

1. `startBackend()` requires `server/index.js` directly in the Electron main process (no separate child process), setting `PORT=3001`.
2. `createWindow()` opens a `BrowserWindow` pointed at `http://localhost:3001`, which serves the built client files.

The app runs identically whether opened in Electron or in a regular browser tab.

Cloud providers do not require a separate transport. Pick the AWS preset, enter the VM public DNS or IP, and connect over SSH like any other remote host.

## Quick Start

```bash
# 1. install all dependencies (server + client)
npm run install:all

# 2. build the client and launch the Electron app
npm start
```

That's it, a window opens with the GUI ready to connect to a remote host.

If you prefer a browser, see [Development workflow](#development-workflow-no-electron) below.

## Scripts

All commands are run from the `gui/` root unless noted otherwise.

| Command | What it does |
|---|---|
| `npm run install:all` | Runs `npm install` in `gui/` to install server and Electron dependencies, then `cd client && npm install` to install frontend dependencies. One command to set up both halves of the project. |
| `npm run build` | Runs `cd client && npx vite build`. Compiles the TypeScript/React source in `client/src/` into static files in `client/dist/` (HTML, CSS, JS bundle). This is the production build of the frontend only, the server needs no build step because it is plain JavaScript. |
| `npm start` | Runs `npm run build && electron .`. First builds the client (see above), then launches Electron. Electron loads `electron/main.js`, which boots the Express server in-process on port 3001 and opens a `BrowserWindow` pointed at `http://localhost:3001`. This is the primary way to run the app. |
| `npm run dist:linux` | Builds release artifacts for Linux (`AppImage` and `.deb`) in `gui/release/`. |
| `npm run dist:win` | Builds a Windows NSIS installer (`.exe`) in `gui/release/`. |
| `npm run dist:linux-win` | Builds both Linux and Windows release artifacts in one command. |

## Release Packaging

All packaging commands are run from `gui/`.

```bash
# Linux artifacts (.AppImage + .deb)
npm run dist:linux

# Windows installer (.exe)
npm run dist:win

# Build Linux + Windows in one run
npm run dist:linux-win
```

Generated files are written to:

```text
gui/release/
```

Typical outputs:

- `Yardstick-<version>.AppImage`
- `yardstick-gui_<version>_amd64.deb`
- `Yardstick Setup <version>.exe`

## Development workflow (without Electron)

For development you don't need Electron at all. Run the server and client in two terminals:

```bash
# terminal 1 -- backend (Express + Socket.IO)
node server/index.js

# terminal 2 -- frontend (Vite dev server with hot reload)
cd client && npm run dev
```

Then open `http://localhost:5173` in a browser. Vite proxies API/socket calls to port 3001.
