```

  ████████╗██████╗ ██████╗ ██╗██╗      ██████╗ ████████╗
  ╚══██╔══╝██╔══██╗██╔══██╗██║██║     ██╔═══██╗╚══██╔══╝
     ██║   ██║  ██║██████╔╝██║██║     ██║   ██║   ██║
     ██║   ██║  ██║██╔═══╝ ██║██║     ██║   ██║   ██║
     ██║   ██████╔╝██║     ██║███████╗╚██████╔╝   ██║
     ╚═╝   ╚═════╝ ╚═╝     ╚═╝╚══════╝ ╚═════╝    ╚═╝

  your AI assistant inside TouchDesigner

```

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-what-it-does">Features</a> •
  <a href="#-all-27-tools">All Tools</a> •
  <a href="#-how-we-compare">Compare</a> •
  <a href="#-deep-dive">Deep Dive</a>
</p>

<br/>

<p align="center">
  <img src="https://img.shields.io/badge/TD_2025-latest-1a1a2e?style=for-the-badge&labelColor=0d0d1a" alt="TD 2025" />
  <img src="https://img.shields.io/badge/27_tools-full_live_control-e94560?style=for-the-badge&labelColor=1a1a2e" alt="27 tools" />
  <img src="https://img.shields.io/badge/POPs-GPU_accelerated-0f3460?style=for-the-badge&labelColor=1a1a2e" alt="POPs" />
  <img src="https://img.shields.io/badge/open_source-MIT-16213e?style=for-the-badge&labelColor=1a1a2e" alt="MIT" />
</p>

<br/>

AI inside TouchDesigner. Full live control. 27 tools, every operator family, TD 2025 POPs included.

It can build things from scratch if you ask — but it really shines when you have an idea and need a tool to keep up. Debug a broken network, trace a signal chain, profile why it's slow, set up expressions, explain a project you just opened, run Python inside TD. Drag the `.tox` in, talk, patch.

It supports **skills** and **memory** — teach it your node patterns, naming conventions, rig layouts, GLSL snippets. It learns how you work and gets better at working with you. A starter skill ships in [`skills/tdpilot-core`](skills/tdpilot-core/SKILL.md) — covers clean layouts, color coding, error checking, visual verification, project versioning, and learning your preferences. Use it as-is or fork it into your own.

**npx tdpilot** → drop the `.tox` → patch. Works with Claude Desktop, Cursor, Claude Code, or any MCP client.

<br/>

```
─── SETUP ────────────────────────────────────────────────────────────
```

<br/>

## 🚀 Quick Start

You need two things running: **TouchDesigner** with the `.tox` loaded, and **Claude Desktop** (or Cursor) pointed at the TDPilot server.

<br/>

### Step 1 — Download this repo

**Option A: ZIP download (no git needed)**
1. Click the green **`<> Code`** button at the top of this page
2. Click **`Download ZIP`**
3. Unzip the folder somewhere you'll remember (e.g. your Desktop or Documents)

**Option B: Git clone**
```bash
git clone https://github.com/dreamrec/touchdesigner-mcp.git
```

<br/>

### Step 2 — TouchDesigner side

1. Open any TouchDesigner project
2. Go to the unzipped folder → open the **`td_component`** folder
3. Drag **`mcp_server.tox`** into your TouchDesigner project
4. That's it — a WebServer starts automatically on port 9981

> 💡 The `.tox` is portable. Drop it into any project you want AI to control.

<br/>

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

<br/>

### Step 4 — Go

1. **Fully quit Claude Desktop** (not just close the window — right-click tray icon → Quit)
2. **Reopen Claude Desktop**
3. Make sure TouchDesigner is running with the `.tox` loaded
4. Ask Claude:

> *"What's in my TouchDesigner project?"*

If Claude responds with your project info, you're connected. 🎉

<br/>

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

<br/>

```
─── FEATURES ─────────────────────────────────────────────────────────
```

<br/>

## 🎛 What It Does

| | |
|---|---|
| 🔨 **Build** | Create any operator with precise positioning, copy, rename, delete |
| 🔌 **Wire** | Connect/disconnect nodes, inspect signal flow |
| 🎚 **Tweak** | Set static values OR live expressions (`absTime.seconds`, CHOP refs, math) |
| 🎯 **POPs** | Full support for TD 2025's GPU-accelerated Point Operators — particles, point clouds, geometry |
| ⚡ **Expressions** | Make networks reactive — parameters that update every frame, not dead snapshots |
| 📸 **See** | Screenshot any TOP, read CHOP channels, inspect SOP/POP geometry |
| 🐍 **Code** | Execute Python inside TD with full stdout/stderr |
| 🐛 **Debug** | Recursive error checking, cook time profiling |
| ⏱ **Timeline** | Play, pause, jump, set FPS |
| 🔍 **Explore** | Search nodes, list operator families, Python introspection |

<br/>

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
| `td_create_node` | Create any operator (TOP, CHOP, SOP, POP, DAT, COMP, MAT) with nodeX/nodeY positioning |
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

<br/>

## 🏗 Architecture

```
   Your AI App          MCP Server             TouchDesigner
  ┌───────────┐      ┌──────────────┐      ┌──────────────────┐
  │  Claude /  │ stdio│   Python     │ HTTP │  WebServer DAT   │
  │  Cursor /  │◄────►│   FastMCP    │◄────►│  on port 9981    │
  │  etc.      │  MCP │   27 tools   │      │  → TD Python API │
  └───────────┘      └──────────────┘      └──────────────────┘
```

<br/>

```
─── COMPARE ──────────────────────────────────────────────────────────
```

<br/>

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
| **POP support (TD 2025)** | ✅ | ❌ | ❌ | ❌ |
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

<br/>

```
─── DEEP DIVE ────────────────────────────────────────────────────────
```

<br/>

## 📖 Deep Dive

> [!NOTE]
> Built for **TouchDesigner 2025** — full support for all latest operator families, GPU-accelerated POPs, new TOPs, DATs, COMPs, and everything in the current release.

<br/>

<!-- ═══════════════════════════════════════════════════════════════ -->

<table><tr><td>

### 🎯 &nbsp; POPs — Point Operators

<sup>GPU-ACCELERATED &nbsp;·&nbsp; TD 2025 &nbsp;·&nbsp; PARTICLES &nbsp;·&nbsp; POINT CLOUDS &nbsp;·&nbsp; SPLINES</sup>

The biggest addition to TouchDesigner in a decade. A completely new operator family that processes **millions of points in real-time on the GPU** — replacing the old CPU-based Particle SOP entirely.

TDPilot creates any POP type (`particlePOP`, `noisePOP`, `transformPOP`, `feedbackPOP`, `DMXFixturePOP`...), sets their parameters and expressions, wires them together, reads their data, and positions them in your network.

If you're doing particles in TD 2025, you should be using POPs — and TDPilot speaks them natively.

</td></tr></table>

<br/>

<!-- ═══════════════════════════════════════════════════════════════ -->

<table><tr><td>

### ⚡ &nbsp; Expressions — Live Parameters

<sup>60 FPS &nbsp;·&nbsp; PYTHON EVAL &nbsp;·&nbsp; REACTIVE &nbsp;·&nbsp; FRAME-BY-FRAME</sup>

Every TD parameter can hold a static value (`seed = 42`) or a **Python expression that re-evaluates every single frame** (`seed = absTime.seconds * 10`).

This is the difference between a frozen snapshot and a living network. TDPilot sets real expressions — tie a parameter to time, to audio input, to another node's output, to a math function — updating 60 times per second.

```python
# static — dead value
{"seed": 42}

# expression — alive, ticking every frame
{"seed": {"expr": "absTime.seconds * 10"}}
{"tx":   {"expr": "op('audio1')['chan1'] * 2"}}
{"rot":  {"expr": "sin(absTime.seconds) * 360"}}
```

Without this, AI-generated networks are dead on arrival.

</td></tr></table>

<br/>

<!-- ═══════════════════════════════════════════════════════════════ -->

<table><tr><td>

### 📐 &nbsp; Node Positioning

<sup>NETWORK LAYOUT &nbsp;·&nbsp; nodeX / nodeY &nbsp;·&nbsp; CLEAN GRAPHS</sup>

Without explicit positioning, every node the AI creates lands at `(0, 0)` — a pile of overlapping boxes you untangle by hand.

TDPilot passes `nodeX` and `nodeY` on creation so the AI lays out clean, readable networks with proper spacing. Sounds small. Matters a lot.

</td></tr></table>

<br/>

<!-- ═══════════════════════════════════════════════════════════════ -->

<table><tr><td>

### 📸 &nbsp; Screenshot TOPs

<sup>VISUAL FEEDBACK &nbsp;·&nbsp; PNG CAPTURE &nbsp;·&nbsp; BASE64 RETURN</sup>

TOPs are TD's image/video operators. TDPilot captures any TOP node as a **PNG** and returns it to the AI as base64 data.

The AI can actually *see* what it's building — check if a noise pattern looks right, verify a composite, inspect a render. It closes the visual feedback loop.

</td></tr></table>

<br/>

<!-- ═══════════════════════════════════════════════════════════════ -->

<table><tr><td>

### 📊 &nbsp; CHOP / SOP Data

<sup>SIGNALS &nbsp;·&nbsp; GEOMETRY &nbsp;·&nbsp; AUDIO &nbsp;·&nbsp; MOTION &nbsp;·&nbsp; VERTICES</sup>

**CHOPs** — channel operators. Audio, motion, LFOs, sensor data. Anything that's a signal over time.
**SOPs** — surface operators. 3D geometry. Points, polygons, meshes.

TDPilot reads CHOP channel values and SOP point positions directly — analyze audio levels, check vertex counts, verify signal chains. Large datasets are auto-downsampled to keep responses fast.

</td></tr></table>

<br/>

<!-- ═══════════════════════════════════════════════════════════════ -->

<table><tr><td>

### 📝 &nbsp; DAT Read / Write

<sup>SCRIPTS &nbsp;·&nbsp; TABLES &nbsp;·&nbsp; JSON &nbsp;·&nbsp; CSV &nbsp;·&nbsp; CONFIG</sup>

DATs are data operators — text files, tables, scripts, JSON, CSV. TDPilot reads from and writes to any DAT.

This is how the AI modifies scripts inside TD, updates lookup tables, or injects configuration data. Table DATs return structured 2D arrays. Text DATs return raw strings.

</td></tr></table>

<br/>

<!-- ═══════════════════════════════════════════════════════════════ -->

<table><tr><td>

### 🔥 &nbsp; Performance Profiling

<sup>COOK TIMES &nbsp;·&nbsp; BOTTLENECKS &nbsp;·&nbsp; SORTED BY SLOWEST</sup>

Every node has a cook time — how long it takes to process each frame. TDPilot reads these timings sorted by slowest node.

Turns *"my project is slow"* into *"your `particle_sim` SOP is taking 14ms per frame."*

</td></tr></table>

<br/>

<!-- ═══════════════════════════════════════════════════════════════ -->

<table><tr><td>

### ⏱ &nbsp; Timeline Control

<sup>PLAY &nbsp;·&nbsp; PAUSE &nbsp;·&nbsp; JUMP &nbsp;·&nbsp; FPS</sup>

Play, pause, jump to a specific frame, change the FPS. Scrub to frame 100 to check state, pause for edits, set FPS for a render pass.

</td></tr></table>

<br/>

<!-- ═══════════════════════════════════════════════════════════════ -->

<table><tr><td>

### 🐛 &nbsp; Recursive Errors

<sup>FULL TREE SCAN &nbsp;·&nbsp; NESTED COMPs &nbsp;·&nbsp; SINGLE CALL</sup>

TD shows errors per-node, but with hundreds of nodes nested in COMPs, finding the broken one is painful.

TDPilot walks the entire node tree recursively, collects every error and warning, returns them in one list with full paths. Every broken node in your project — one call.

</td></tr></table>

<br/>

<!-- ═══════════════════════════════════════════════════════════════ -->

<table><tr><td>

### 🐍 &nbsp; Python Execution

<sup>ARBITRARY CODE &nbsp;·&nbsp; FULL API ACCESS &nbsp;·&nbsp; STDOUT CAPTURE</sup>

Run arbitrary Python inside TD's runtime — `op()`, `project`, `absTime`, `tdu`, everything.

The escape hatch. If there's no dedicated tool for something, the AI writes and executes the Python directly. Stdout and stderr captured and returned.

</td></tr></table>

<br/>

<!-- ═══════════════════════════════════════════════════════════════ -->

<table><tr><td>

### 🛡 &nbsp; Input Validation

<sup>PYDANTIC &nbsp;·&nbsp; TYPE CHECKING &nbsp;·&nbsp; PRE-TD ERROR CATCHING</sup>

Every tool input is validated with **Pydantic** before it reaches TouchDesigner. Wrong types, missing fields, invalid values — caught with clear error messages at the MCP layer instead of crashing inside TD.

</td></tr></table>

<br/>

<!-- ═══════════════════════════════════════════════════════════════ -->

<table><tr><td>

### 📦 &nbsp; Portable .tox

<sup>SINGLE FILE &nbsp;·&nbsp; ZERO DEPENDENCIES &nbsp;·&nbsp; DRAG AND DROP</sup>

The entire TD-side component is a single `.tox` file. No file dependencies, no external scripts, no paths to configure. Contains the WebServer DAT, the callbacks, everything.

Move it between projects, share it, back it up — it just works.

</td></tr></table>

<br/>

```
─── EXTRAS ───────────────────────────────────────────────────────────
```

<br/>

## 📜 License

MIT — do whatever you want.

<br/>

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

<br/>

---

<br/>

```


    ██████╗ ██████╗ ███████╗ █████╗ ███╗   ███╗██████╗ ███████╗ ██████╗
    ██╔══██╗██╔══██╗██╔════╝██╔══██╗████╗ ████║██╔══██╗██╔════╝██╔════╝
    ██║  ██║██████╔╝█████╗  ███████║██╔████╔██║██████╔╝█████╗  ██║
    ██║  ██║██╔══██╗██╔══╝  ██╔══██║██║╚██╔╝██║██╔══██╗██╔══╝  ██║
    ██████╔╝██║  ██║███████╗██║  ██║██║ ╚═╝ ██║██║  ██║███████╗╚██████╗
    ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝

    ██╗      █████╗ ██████╗ ███████╗  ™
    ██║     ██╔══██╗██╔══██╗██╔════╝
    ██║     ███████║██████╔╝███████╗
    ██║     ██╔══██║██╔══██╗╚════██║
    ███████╗██║  ██║██████╔╝███████║
    ╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝


```
