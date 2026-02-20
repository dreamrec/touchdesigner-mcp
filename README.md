```

        ╔══════════════════════════════════════════════════════════════════╗
        ║                                                                ║
        ║    ████████╗██████╗ ██████╗ ██╗██╗      ██████╗ ████████╗     ║
        ║    ╚══██╔══╝██╔══██╗██╔══██╗██║██║     ██╔═══██╗╚══██╔══╝     ║
        ║       ██║   ██║  ██║██████╔╝██║██║     ██║   ██║   ██║        ║
        ║       ██║   ██║  ██║██╔═══╝ ██║██║     ██║   ██║   ██║        ║
        ║       ██║   ██████╔╝██║     ██║███████╗╚██████╔╝   ██║        ║
        ║       ╚═╝   ╚═════╝ ╚═╝     ╚═╝╚══════╝ ╚═════╝    ╚═╝        ║
        ║                                                                ║
        ║    build & control touchdesigner with ai                       ║
        ║    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    ║
        ║    27 tools  ·  expressions  ·  live control  ·  open source   ║
        ║                                                                ║
        ╚══════════════════════════════════════════════════════════════════╝

              ○───────┐                           ┌───────○
              │ input │    ┌───────────────┐      │output │
              ○───────┘    │  ◉  mcp  ◉    │      └───────○
                     ╰─────┤   server      ├─────╯
                           │  \_______/    │
                           └──────┬────────┘
                                  │
                              ┌───┴───┐
                              │ ░░░░░ │
                              └───────┘
```

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-what-it-does">Features</a> •
  <a href="#-all-27-tools">All Tools</a> •
  <a href="#-how-we-compare">Compare</a>
</p>

---

**Build and control TouchDesigner with AI.**

Create nodes, wire networks, set live expressions, read CHOP data, screenshot TOPs, inspect geometry, profile cook times, execute Python, control the timeline — 27 tools that turn a conversation into a living TD project. Expressions tick every frame. Nodes land exactly where you place them. Parameters tell you if they're constant or driven.

`npx tdpilot` → drop the `.tox` → talk.

Works with **Claude Desktop**, **Cursor**, **Claude Code**, or any MCP client.

---

## 🚀 Quick Start

You need two things running: **TouchDesigner** with the `.tox` loaded, and **Claude Desktop** (or Cursor) pointed at the TDPilot server.

---

### Step 1 — Download this repo

**Option A: ZIP download (no git needed)**
1. Click the green **`<> Code`** button at the top of this page
2. Click **`Download ZIP`**
3. Unzip the folder somewhere you'll remember (e.g. your Desktop or Documents)

**Option B: Git clone**
```bash
git clone https://github.com/dreamrec/touchdesigner-mcp.git
```

---

### Step 2 — TouchDesigner side

1. Open any TouchDesigner project
2. Go to the unzipped folder → open the **`td_component`** folder
3. Drag **`mcp_server.tox`** into your TouchDesigner project
4. That's it — a WebServer starts automatically on port 9981

> 💡 The `.tox` is portable. Drop it into any project you want AI to control.

---

### Step 3 — Claude Desktop side

Pick whichever method works for you:

#### 🟢 Easiest: npx (if you have Node.js)

Open Claude Desktop config file:
- **Windows:** press `Win + R`, type `notepad %APPDATA%\Claude\claude_desktop_config.json`, hit Enter
- **macOS:** open Terminal, type `open ~/Library/Application\ Support/Claude/claude_desktop_config.json`

Paste this and save:

```json
{
  "mcpServers": {
    "touchdesigner": {
      "command": "npx",
      "args": ["-y", "tdpilot"]
    }
  }
}
```

That's it. npx downloads everything automatically on first run.

#### 🔵 One-click installer (no Node.js needed)

Open a terminal **inside the unzipped folder** and run:

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File install.ps1
```

```bash
# macOS (Terminal)
bash install.sh
```

This installs `uv`, configures Claude Desktop, and backs up your existing config.

---

### Step 4 — Go

1. **Fully quit Claude Desktop** (not just close the window — right-click tray icon → Quit)
2. **Reopen Claude Desktop**
3. Make sure TouchDesigner is running with the `.tox` loaded
4. Ask Claude:

> *"What's in my TouchDesigner project?"*

If Claude responds with your project info, you're connected. 🎉

---

<details>
<summary><strong>⚠️ Troubleshooting</strong></summary>
<br/>

**Claude says it can't connect to TouchDesigner:**
- Is TouchDesigner running?
- Did you drag the `.tox` into your project?
- Check that the WebServer DAT inside `mcp_server` is set to Active and port 9981

**Windows: "path not found" errors:**
- Use double backslashes in paths: `C:\\Users\\you\\touchdesigner-mcp`
- If your Desktop is on OneDrive, the path may be `C:\Users\you\OneDrive\Desktop\...`

**Config file doesn't exist yet:**
- Open Claude Desktop at least once first — it creates the config file on first launch
- If the file is empty, paste the full JSON block from above

**Multiple MCP servers:**
- If you already have other servers in your config, add `touchdesigner` inside the existing `mcpServers` block — don't create a second one

</details>

<details>
<summary><strong>Other clients (Cursor, Claude Code)</strong></summary>
<br/>

**Cursor** — add to `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "touchdesigner": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/touchdesigner-mcp", "touchdesigner-mcp"],
      "env": { "TD_MCP_HOST": "127.0.0.1", "TD_MCP_PORT": "9981" }
    }
  }
}
```

**Claude Code:**
```bash
claude mcp add touchdesigner -- uv run --directory /path/to/touchdesigner-mcp touchdesigner-mcp
```

</details>

---

## 🎛 What It Does

| | |
|---|---|
| 🔨 **Build** | Create any operator with precise positioning, copy, rename, delete |
| 🔌 **Wire** | Connect/disconnect nodes, inspect signal flow |
| 🎚 **Tweak** | Set static values OR live expressions (`absTime.seconds`, CHOP refs, math) |
| ⚡ **Expressions** | Make networks reactive — parameters that update every frame, not dead snapshots |
| 📸 **See** | Screenshot any TOP, read CHOP channels, inspect SOP geometry |
| 🐍 **Code** | Execute Python inside TD with full stdout/stderr |
| 🐛 **Debug** | Recursive error checking, cook time profiling |
| ⏱ **Timeline** | Play, pause, jump, set FPS |
| 🔍 **Explore** | Search nodes, list operator families, Python introspection |

---

## 🔧 All 27 Tools

<details>
<summary><strong>Scene & Info</strong> — 4 tools</summary>

| Tool | Does |
|------|------|
| `td_get_info` | Version, FPS, project name, timeline state |
| `td_list_families` | All operator families and types in the project |
| `td_timeline` | Current frame, seconds, play state |
| `td_timeline_set` | Play, pause, jump to frame, change FPS |

</details>

<details>
<summary><strong>Nodes</strong> — 7 tools</summary>

| Tool | Does |
|------|------|
| `td_get_nodes` | List children of any COMP with filtering |
| `td_get_node_detail` | Full detail — params, connections, errors |
| `td_search_nodes` | Find nodes by name, type, or family |
| `td_create_node` | Create any operator type with optional nodeX/nodeY positioning |
| `td_delete_node` | Remove a node |
| `td_copy_node` | Duplicate a node |
| `td_rename_node` | Rename a node |

</details>

<details>
<summary><strong>Parameters</strong> — 3 tools</summary>

| Tool | Does |
|------|------|
| `td_get_params` | Read params with expression/mode info, filter by page or name |
| `td_set_params` | Set static values OR live expressions (`{"seed": {"expr": "absTime.seconds"}}`) |
| `td_pulse_param` | Trigger pulse params (Cook, Reset) |

</details>

<details>
<summary><strong>Wiring</strong> — 3 tools</summary>

| Tool | Does |
|------|------|
| `td_connect_nodes` | Wire output → input |
| `td_disconnect` | Disconnect a connector |
| `td_get_connections` | See all inputs/outputs of a node |

</details>

<details>
<summary><strong>Data</strong> — 5 tools</summary>

| Tool | Does |
|------|------|
| `td_screenshot` | Capture any TOP as PNG |
| `td_chop_data` | Read CHOP channels (auto-downsampled) |
| `td_sop_data` | Read SOP points and primitives |
| `td_get_content` | Read text/table DAT content |
| `td_set_content` | Write to text/table DATs |

</details>

<details>
<summary><strong>Code & Debug</strong> — 5 tools</summary>

| Tool | Does |
|------|------|
| `td_exec_python` | Run Python in TD with stdout capture |
| `td_python_help` | Python help() for any TD class |
| `td_python_classes` | List all TD Python classes |
| `td_get_errors` | Errors and warnings (recursive) |
| `td_cooking_info` | Cook times sorted by slowest node |

</details>

---

## 🏗 Architecture

```
   Your AI App          MCP Server             TouchDesigner
  ┌───────────┐      ┌──────────────┐      ┌──────────────────┐
  │  Claude /  │ stdio│   Python     │ HTTP │  WebServer DAT   │
  │  Cursor /  │◄────►│   FastMCP    │◄────►│  on port 9981    │
  │  etc.      │  MCP │   27 tools   │      │  → TD Python API │
  └───────────┘      └──────────────┘      └──────────────────┘
```

---

## 📊 How We Compare

| | **TDPilot** | [8beeeaaat](https://github.com/8beeeaaat/touchdesigner-mcp) | [satoruhiga](https://github.com/satoruhiga/claude-touchdesigner) | [bottobot](https://github.com/bottobot/touchdesigner-mcp-server) |
|---|:---:|:---:|:---:|:---:|
| **Tools** | **27** | 12 | ~6 | 0 |
| **Live control** | ✅ | ✅ | ✅ | ❌ |
| **CRUD + copy + rename** | ✅ | partial | partial | ❌ |
| **Wire / disconnect** | ✅ | ✅ | ✅ | ❌ |
| **Expressions (live params)** | ✅ | ❌ | ❌ | ❌ |
| **Node positioning** | ✅ | ❌ | ❌ | ❌ |
| **Screenshot TOPs** | ✅ | ❌ | ❌ | ❌ |
| **CHOP / SOP data** | ✅ | ❌ | ❌ | ❌ |
| **DAT read / write** | ✅ | ❌ | ❌ | ❌ |
| **Performance profiling** | ✅ | ❌ | ❌ | ❌ |
| **Timeline control** | ✅ | ❌ | ❌ | ❌ |
| **Python execution** | ✅ | ✅ | ✅ | ❌ |
| **Recursive errors** | ✅ | ✅ | ❌ | ❌ |
| **Input validation** | ✅ Pydantic | ❌ | ❌ | ❌ |
| **npm install** | ✅ `npx tdpilot` | ✅ | ❌ | ✅ |
| **One-click installer** | ✅ | ❌ | ❌ | ❌ |
| **Portable .tox** | ✅ | ✅ | ❌ | N/A |

---

## 📖 What These Features Actually Mean

**Expressions (live params)** — In TouchDesigner, every parameter can either hold a static value (`seed = 42`) or a Python expression that TD re-evaluates every single frame (`seed = absTime.seconds * 10`). This is the difference between a frozen snapshot and a living, reactive network. TDPilot lets the AI set real expressions — tie a parameter to time, to audio input, to another node's output, to a math function — and it updates 60 times per second. Without this, AI-generated networks are dead on arrival.

**Node positioning** — When you create nodes in TouchDesigner, they get placed somewhere in the network editor. Without explicit positioning, every node the AI creates lands at (0, 0) — a pile of overlapping boxes you have to untangle by hand. TDPilot passes `nodeX` and `nodeY` on creation so the AI can lay out clean, readable networks with proper spacing. Sounds small, matters a lot.

**Screenshot TOPs** — TOPs are TouchDesigner's image/video operators. TDPilot can capture any TOP node as a PNG and return it to the AI as base64 data. This means the AI can actually *see* what it's building — check if a noise pattern looks right, verify a composite, inspect a render. It closes the visual feedback loop.

**CHOP / SOP data** — CHOPs are channel operators (audio, motion, LFOs, sensor data — anything that's a signal over time). SOPs are surface operators (3D geometry — points, polygons, meshes). TDPilot can read CHOP channel values and SOP point positions directly, so the AI can analyze audio levels, check geometry vertex counts, or verify that a signal chain is producing the expected output. Large datasets are automatically downsampled to keep responses fast.

**DAT read / write** — DATs are data operators (text files, tables, scripts, JSON, CSV). TDPilot can read from and write to any DAT. This is how the AI modifies scripts inside TD, updates lookup tables, or injects configuration data. For table DATs it returns structured 2D arrays; for text DATs it returns the raw string.

**Performance profiling** — Every node in TD has a cook time — how long it takes to process each frame. TDPilot reads these timings and returns them sorted by slowest node. When a project is dropping frames, the AI can pinpoint the bottleneck: a heavy SOP, an unoptimized GLSL shader, a bloated Python script. It turns "my project is slow" into "your `particle_sim` SOP is taking 14ms per frame."

**Timeline control** — Play, pause, jump to a specific frame, change the FPS. Simple but essential for any automated workflow — scrub to frame 100 to check a specific state, pause to make edits without the network cooking, set FPS for a render pass.

**Recursive errors** — TouchDesigner shows errors per-node, but when a network has hundreds of nodes nested inside COMPs, finding the broken one is painful. TDPilot walks the entire node tree recursively, collects every error and warning, and returns them in one list with full paths. The AI sees every broken node in your project in a single call.

**Python execution** — Run arbitrary Python code inside TD's runtime with full access to `op()`, `project`, `absTime`, `tdu`, and every other TD Python object. Stdout and stderr are captured and returned. This is the escape hatch — if there's no dedicated tool for something, the AI can write and execute the Python to do it directly.

**Input validation (Pydantic)** — Every tool input is validated with Pydantic models before it reaches TouchDesigner. Wrong types, missing fields, and invalid values get caught with clear error messages at the MCP layer instead of crashing inside TD. This means fewer cryptic errors and more useful feedback when something goes wrong.

**Portable .tox** — The entire TD-side component is a single `.tox` file you drag into any project. No file dependencies, no external scripts, no paths to configure. It contains the WebServer DAT, the callbacks, everything. Move it between projects, share it with collaborators, back it up — it just works.

---

## 📜 License

MIT — do whatever you want.

---

<details>
<summary>Advanced: Alternative TD Setup</summary>
<br/>

If you don't want to use the `.tox`:

1. Open TouchDesigner → Dialogs → Textport
2. Paste `setup_mcp_in_td.py` contents and press Enter

Or manually: create a Base COMP named `mcp_server`, add a WebServer DAT on port 9981, add a Text DAT named `callbacks` with `td_component/mcp_webserver_callbacks.py`, and set the WebServer's Callbacks to `callbacks`.

</details>

<details>
<summary>Environment Variables</summary>
<br/>

| Variable | Default | Description |
|----------|---------|-------------|
| `TD_MCP_HOST` | `127.0.0.1` | TouchDesigner host |
| `TD_MCP_PORT` | `9981` | WebServer DAT port |

</details>

---

```


    ·bg`                                                                      .d·
    ·Bg`    ██████▄  ██▀███  ▓█████ ▄▄▄       ███▄ ▄███▓██▀███  ▓█████  ▄████▄
    ·bg`    ▒██▀ ██▌▓██ ▒ ██▒▓█   ▀▒████▄    ▓██▒▀█▀ ██▒▓██ ▒ ██▒▓█   ▀ ▒██▀ ▀█
    ·bg`    ░██   █▌▓██ ░▄█ ▒▒███  ▒██  ▀█▄  ▓██    ▓██░▓██ ░▄█ ▒▒███   ▒▓█    ▄
    ·bg`    ░▓█▄   ▌▒██▀▀█▄  ▒▓█  ▄░██▄▄▄▄██ ▒██    ▒██ ▒██▀▀█▄  ▒▓█  ▄▒▓▓▄ ▄██▒
    ·bg`    ░▒████▓ ░██▓ ▒██▒░▒████▒▓█   ▓██▒▒██▒   ░██▒░██▓ ▒██▒░▒████▒▒ ▓███▀ ░
    ·bg`     ▒▒▓  ▒ ░ ▒▓ ░▒▓░░░ ▒░ ░▒▒   ▓▒█░░ ▒░   ░  ░░ ▒▓ ░▒▓░░░ ▒░ ░░ ░▒ ▒  ░
    ·bg`     ░ ▒  ▒   ░▒ ░ ▒░ ░ ░  ░ ▒   ▒▒ ░░ ░      ░  ░▒ ░ ▒░ ░ ░  ░  ░  ▒
    ·bg`     ░ ░  ░   ░░   ░    ░    ░   ▒     ░      ░  ░░   ░    ░   ░
    ·Bg`       ░       ░        ░        ░            ░   ░        ░        ░
    ·Bg`                                                                      ·Bg`
    ·BG`              ██▓    ▄▄▄       ▄▄▄▄     ██████                        ·BG`
    ·BG`             ▓██▒   ▒████▄    ▓█████▄ ▒██    ▒                        ·BG`
    ·BG`             ▒██░   ▒██  ▀█▄  ▒██▒ ▄██░ ▓██▄                         ·BG`
    ·BG`             ░██░   ░██▄▄▄▄██ ▒██░█▀    ▒   ██▒                      ·BG`
    ·BG`             ░██░    ▓█   ▓██▒░▓█  ▀█▓▒██████▒▒                      ·BG`
    ·BG`             ░▓      ▒▒   ▓▒█░░▒▓███▀▒▒ ▒▓▒ ▒ ░                      ·BG`
    ·bg`                                                                      ·bg`
    ·bg`    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    ·bg`
    ·bg`                  where  machines  dream  to  learn                    ·bg`
    ·bg`    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    ·bg`
    ·bg`                                                                      ·bg`
    ·bg`                       github.com/dreamrec                            ·bg`
    `··                                                                        ··`

```
