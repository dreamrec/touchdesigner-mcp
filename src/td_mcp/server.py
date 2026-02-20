#!/usr/bin/env python3
"""
TouchDesigner MCP Server
========================
A comprehensive MCP server for live control of TouchDesigner via the
WebServer DAT bridge. Enables AI agents to create, inspect, connect,
and manipulate nodes, execute Python, capture images, and more.

Architecture:
    AI Client (Claude, Cursor, etc.)
        ↕ MCP protocol (stdio)
    This Server (FastMCP + httpx)
        ↕ HTTP to localhost:9981
    TouchDesigner WebServer DAT
        ↕ TD Python API
    TouchDesigner Scene

Usage:
    python -m td_mcp.server
    # or via uv:
    uv run python -m td_mcp.server

Requires TouchDesigner 2025.30000+ with the MCP WebServer component active.
"""

import json
import os
import sys
import logging
import base64
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP, Context

from td_mcp.td_client import TDClient, TouchDesignerConnectionError, TouchDesignerAPIError
from td_mcp.models import (
    ResponseFormat,
    GetNodesInput, NodePathInput, GetParamsInput, SetParamsInput,
    CreateNodeInput, DeleteNodeInput, CopyNodeInput, RenameNodeInput,
    ConnectNodesInput, DisconnectInput,
    GetContentInput, SetContentInput,
    ExecPythonInput,
    ScreenshotInput,
    CHOPDataInput, SOPDataInput,
    CookingInfoInput,
    SearchNodesInput,
    PythonHelpInput,
    TimelineSetInput,
    PulseParamInput,
    GetErrorsInput,
)

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

TD_HOST = os.environ.get("TD_MCP_HOST", "127.0.0.1")
TD_PORT = int(os.environ.get("TD_MCP_PORT", "9981"))

logger = logging.getLogger("td_mcp")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,  # MCP servers must log to stderr, not stdout
)

# ─────────────────────────────────────────────────────────────
# Lifespan — persistent HTTP client
# ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def server_lifespan(app):
    """Initialize and clean up the TD HTTP client."""
    client = TDClient(host=TD_HOST, port=TD_PORT)
    logger.info(f"TouchDesigner MCP server starting — connecting to {TD_HOST}:{TD_PORT}")

    try:
        health = await client.health_check()
        logger.info(f"TouchDesigner connection OK: {health}")
    except TouchDesignerConnectionError:
        logger.warning(
            f"TouchDesigner not reachable at {TD_HOST}:{TD_PORT}. "
            "Tools will retry when called. Start TD and activate the MCP WebServer component."
        )

    yield {"td_client": client}

    await client.close()
    logger.info("TouchDesigner MCP server stopped.")


# ─────────────────────────────────────────────────────────────
# FastMCP Server
# ─────────────────────────────────────────────────────────────

mcp = FastMCP(
    "touchdesigner_mcp",
    lifespan=server_lifespan,
)


def _get_client(ctx: Context) -> TDClient:
    """Extract the TDClient from lifespan context."""
    return ctx.request_context.lifespan_context["td_client"]


def _handle_error(e: Exception) -> str:
    """Consistent error formatting."""
    if isinstance(e, TouchDesignerConnectionError):
        return (
            f"Error: Cannot connect to TouchDesigner. {str(e)}\n\n"
            "Troubleshooting:\n"
            "1. Is TouchDesigner running?\n"
            "2. Is the MCP WebServer component imported and active?\n"
            "3. Is port 9981 correct? (check with: lsof -i :9981)\n"
            "4. Try restarting TouchDesigner."
        )
    elif isinstance(e, TouchDesignerAPIError):
        msg = f"Error: {str(e)}"
        if e.details:
            if 'traceback' in e.details:
                msg += f"\n\nTD Traceback:\n{e.details['traceback']}"
        return msg
    return f"Error: {type(e).__name__}: {str(e)}"


def _format_nodes_markdown(nodes: list, title: str = "Nodes") -> str:
    """Format a list of node dicts as readable markdown."""
    if not nodes:
        return f"No {title.lower()} found."

    lines = [f"## {title} ({len(nodes)})\n"]
    for n in nodes:
        icon = {"TOP": "🖼", "CHOP": "📊", "SOP": "🔷", "DAT": "📄", "COMP": "📦", "MAT": "🎨"}.get(n.get('family', ''), "•")
        lines.append(f"- {icon} **{n['name']}** `{n['path']}` — {n['type']}")
        if n.get('errors'):
            lines.append(f"  ⚠️ Error: {n['errors']}")
    return "\n".join(lines)


def _format_params_markdown(params: dict, path: str) -> str:
    """Format parameters as readable markdown."""
    if not params:
        return f"No parameters found for `{path}`."

    lines = [f"## Parameters for `{path}`\n"]
    current_page = None
    for name, info in sorted(params.items(), key=lambda x: (x[1].get('page', ''), x[0])):
        page = info.get('page', '')
        if page != current_page:
            current_page = page
            lines.append(f"\n### {page or 'Default'}\n")
        val = info.get('value', '')
        default = info.get('default', '')
        label = info.get('label', name)
        marker = " *(modified)*" if val != default else ""
        lines.append(f"- **{label}** (`{name}`): `{val}`{marker}")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# TOOLS — Environment & Info
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="td_get_info",
    annotations={
        "title": "Get TouchDesigner Info",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def td_get_info(ctx: Context) -> str:
    """Get TouchDesigner environment info: version, build, project name, FPS, frame, timeline state.

    Use this tool first to verify the connection to TouchDesigner is working
    and to understand the current project state.

    Returns:
        str: JSON with version, build, osName, project_name, fps, frame, timeline range, etc.
    """
    try:
        client = _get_client(ctx)
        data = await client.request("info")
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="td_list_families",
    annotations={
        "title": "List Operator Families & Types",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def td_list_families(ctx: Context) -> str:
    """List all operator families (TOP, CHOP, SOP, DAT, COMP, MAT) and the specific
    node types present in the current project. Useful for discovering what operators
    are available before creating new nodes.

    Returns:
        str: JSON mapping each family to a list of operator types found in the project.
    """
    try:
        client = _get_client(ctx)
        data = await client.request("families")
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


# ═══════════════════════════════════════════════════════════════
# TOOLS — Node Navigation & Inspection
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="td_get_nodes",
    annotations={
        "title": "List Child Nodes",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def td_get_nodes(params: GetNodesInput, ctx: Context) -> str:
    """List children of a COMP node at the given path, with optional family/type filtering.

    Use this to explore the node graph. Start from '/' or '/project1' and drill down.
    Supports pagination for large networks.

    Args:
        params: path (str), family (optional), type (optional), include_params (bool),
                limit (int), offset (int), response_format

    Returns:
        str: JSON with nodes array, total count, pagination info.
             Each node has: name, path, type, family, errors, warnings.
    """
    try:
        client = _get_client(ctx)
        data = await client.request("nodes", params.model_dump(exclude={'response_format'}, exclude_none=True))

        if params.response_format == ResponseFormat.MARKDOWN:
            return _format_nodes_markdown(data.get('nodes', []), f"Children of {params.path}")

        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="td_get_node_detail",
    annotations={
        "title": "Get Node Detail",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def td_get_node_detail(params: NodePathInput, ctx: Context) -> str:
    """Get comprehensive detail about a single node: all parameters, connections,
    errors, position, and child count (if COMP).

    Args:
        params: path (str) — absolute path to the node

    Returns:
        str: JSON with full node info including parameters dict, inputs/outputs
             connection lists, errors, warnings, and child info for COMPs.
    """
    try:
        client = _get_client(ctx)
        data = await client.request("node/detail", {"path": params.path})

        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [f"## {data.get('name', '?')} (`{data.get('path', '?')}`)\n"]
            lines.append(f"- **Type**: {data.get('type', '?')} ({data.get('family', '?')})")
            if data.get('errors'):
                lines.append(f"- ⚠️ **Errors**: {data['errors']}")
            if data.get('inputs'):
                lines.append(f"- **Inputs**: {len(data['inputs'])} connections")
            if data.get('outputs'):
                lines.append(f"- **Outputs**: {len(data['outputs'])} connections")
            if data.get('children_count'):
                lines.append(f"- **Children**: {data['children_count']}")
            if data.get('parameters'):
                lines.append(_format_params_markdown(data['parameters'], data['path']))
            return "\n".join(lines)

        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="td_get_params",
    annotations={
        "title": "Get Node Parameters",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def td_get_params(params: GetParamsInput, ctx: Context) -> str:
    """Get parameters of a specific node, optionally filtered by page or parameter names.

    Each parameter includes: value, default, label, style, readOnly flag,
    isPulse, isMenu, and menu options if applicable.

    Args:
        params: path (str), page (optional str), names (optional list of str)

    Returns:
        str: JSON with parameters dict keyed by parameter name.
    """
    try:
        client = _get_client(ctx)
        body = params.model_dump(exclude={'response_format'}, exclude_none=True)
        data = await client.request("node/params", body)

        if params.response_format == ResponseFormat.MARKDOWN:
            return _format_params_markdown(data.get('parameters', {}), params.path)

        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="td_set_params",
    annotations={
        "title": "Set Node Parameters",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def td_set_params(params: SetParamsInput, ctx: Context) -> str:
    """Set one or more parameters on a node.

    Pass a dictionary of parameter names to their new values.
    Each parameter is set independently — partial success is possible.

    Supports three modes:
    - Static value (plain): {"seed": 42, "amp": 0.5}
    - Expression (live, updates every frame): {"seed": {"expr": "absTime.seconds * 10"}}
    - Explicit static: {"seed": {"val": 42}}

    Use EXPRESSIONS to make networks reactive and alive:
    - Time-based: {"tx": {"expr": "absTime.seconds * 0.1"}}
    - CHOP reference: {"scale": {"expr": "op('audio1')['chan1']"}}
    - Math: {"rotate": {"expr": "sin(absTime.seconds) * 360"}}
    - Other node ref: {"seed": {"expr": "op('lfo1').par.amp.eval()"}}

    Args:
        params: path (str), params (dict of param_name → value or {expr: str})
                Example: {"path": "/project1/noise1", "params": {"seed": {"expr": "absTime.seconds * 10"}, "amp": 0.5}}

    Returns:
        str: JSON with results for each parameter (success/failure + mode + value).
    """
    try:
        client = _get_client(ctx)
        data = await client.request("node/params/set", params.model_dump())
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


# ═══════════════════════════════════════════════════════════════
# TOOLS — Node Creation / Deletion / Copy / Rename
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="td_create_node",
    annotations={
        "title": "Create Node",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def td_create_node(params: CreateNodeInput, ctx: Context) -> str:
    """Create a new operator node in TouchDesigner.

    Common operator types:
    - TOPs: noiseTOP, levelTOP, nullTOP, compositeTOP, feedbackTOP, moviefileinTOP, renderTOP
    - CHOPs: waveCHOP, noiseCHOP, nullCHOP, mathCHOP, constantCHOP, selectCHOP, mergeCHOP
    - SOPs: sphereSOP, boxSOP, gridSOP, lineSOP, nullSOP, transformSOP, noiseSOP, mergeSOP
    - DATs: textDAT, tableDAT, scriptDAT, nullDAT, selectDAT, chopexecDAT, webserverDAT
    - COMPs: baseCOMP, containerCOMP, geometryCOMP, cameraCOMP, lightCOMP
    - MATs: pbrMAT, phongMAT, wireframeMAT, constMAT

    Use nodeX/nodeY to position nodes in the network editor for readability.
    Space nodes ~200px apart horizontally, ~200px apart vertically for clean layouts.

    Args:
        params: parent_path (str), node_type (str), name (optional str),
                nodeX (optional int), nodeY (optional int)

    Returns:
        str: JSON with success flag and created node info (name, path, type, family, position).
    """
    try:
        client = _get_client(ctx)
        data = await client.request("node/create", params.model_dump(exclude_none=True))
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="td_delete_node",
    annotations={
        "title": "Delete Node",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def td_delete_node(params: DeleteNodeInput, ctx: Context) -> str:
    """Delete a node from TouchDesigner. This is irreversible.

    Args:
        params: path (str) — absolute path to the node to destroy

    Returns:
        str: JSON with success flag and deleted node info.
    """
    try:
        client = _get_client(ctx)
        data = await client.request("node/delete", params.model_dump())
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="td_copy_node",
    annotations={
        "title": "Copy/Duplicate Node",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def td_copy_node(params: CopyNodeInput, ctx: Context) -> str:
    """Duplicate/copy a node, optionally into a different parent COMP.

    Args:
        params: source_path (str), dest_parent (optional str), new_name (optional str)

    Returns:
        str: JSON with success flag and new node info.
    """
    try:
        client = _get_client(ctx)
        data = await client.request("node/copy", params.model_dump(exclude_none=True))
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="td_rename_node",
    annotations={
        "title": "Rename Node",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def td_rename_node(params: RenameNodeInput, ctx: Context) -> str:
    """Rename a node.

    Args:
        params: path (str), new_name (str)

    Returns:
        str: JSON with old name, new name, and updated path.
    """
    try:
        client = _get_client(ctx)
        data = await client.request("node/rename", params.model_dump())
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


# ═══════════════════════════════════════════════════════════════
# TOOLS — Connections / Wiring
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="td_connect_nodes",
    annotations={
        "title": "Connect Nodes",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def td_connect_nodes(params: ConnectNodesInput, ctx: Context) -> str:
    """Wire the output of one node to the input of another.

    Nodes must be of the same family (TOP→TOP, CHOP→CHOP, etc.) or
    use bridge operators (e.g. CHOPtoTOP, TOPtoCHOP).

    Args:
        params: source_path (str), target_path (str),
                source_index (int, default 0), target_index (int, default 0)

    Returns:
        str: JSON with success flag and connection details.
    """
    try:
        client = _get_client(ctx)
        data = await client.request("node/connect", params.model_dump())
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="td_disconnect",
    annotations={
        "title": "Disconnect Node",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def td_disconnect(params: DisconnectInput, ctx: Context) -> str:
    """Disconnect a node's input or output connector.

    Args:
        params: path (str), connector_type ('input' or 'output'), index (int)

    Returns:
        str: JSON with success flag.
    """
    try:
        client = _get_client(ctx)
        data = await client.request("node/disconnect", params.model_dump())
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="td_get_connections",
    annotations={
        "title": "Get Node Connections",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def td_get_connections(params: NodePathInput, ctx: Context) -> str:
    """Get all input and output connections for a node.

    Returns which nodes are connected to each input/output connector,
    useful for understanding the signal flow in a network.

    Args:
        params: path (str)

    Returns:
        str: JSON with 'inputs' and 'outputs' arrays showing connected node paths and indices.
    """
    try:
        client = _get_client(ctx)
        data = await client.request("node/connections", {"path": params.path})
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


# ═══════════════════════════════════════════════════════════════
# TOOLS — DAT Content Read/Write
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="td_get_content",
    annotations={
        "title": "Read DAT Content",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def td_get_content(params: GetContentInput, ctx: Context) -> str:
    """Read text or table content from a DAT node (Text DAT, Table DAT, Script DAT, etc.).

    For table DATs: returns a 2D array of cell values.
    For text DATs: returns the raw text string.

    Args:
        params: path (str) — path to a DAT node

    Returns:
        str: JSON with format ('text' or 'table') and the content data.
    """
    try:
        client = _get_client(ctx)
        data = await client.request("node/content", params.model_dump())
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="td_set_content",
    annotations={
        "title": "Write DAT Content",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def td_set_content(params: SetContentInput, ctx: Context) -> str:
    """Write text or table content to a DAT node.

    Provide either 'text' (for Text/Script DATs) or 'table' (2D array for Table DATs).

    Args:
        params: path (str), text (optional str), table (optional 2D list of strings)

    Returns:
        str: JSON with success flag and content length.
    """
    try:
        client = _get_client(ctx)
        data = await client.request("node/content/set", params.model_dump(exclude_none=True))
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


# ═══════════════════════════════════════════════════════════════
# TOOLS — Python Execution
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="td_exec_python",
    annotations={
        "title": "Execute Python in TouchDesigner",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def td_exec_python(params: ExecPythonInput, ctx: Context) -> str:
    """Execute arbitrary Python code inside TouchDesigner's Python environment.

    The code runs with full access to TD's Python API: op(), ops(), project, app,
    absTime, me, parent(), mod, ui, tdu.

    To return a value from the code, assign it to the special variable '__result__':
        __result__ = op('/project1/noise1').par.seed.eval()

    Captured stdout and stderr are included in the response.

    ⚠️ This is a powerful tool — use with care. Avoid infinite loops or
    operations that could freeze TouchDesigner.

    Args:
        params: code (str) — Python code to execute

    Returns:
        str: JSON with success flag, result value, stdout, and stderr.
             On error: error message, type, traceback.
    """
    try:
        client = _get_client(ctx)
        data = await client.request("exec", params.model_dump())
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


# ═══════════════════════════════════════════════════════════════
# TOOLS — Screenshot / Visual Capture
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="td_screenshot",
    annotations={
        "title": "Capture TOP as Image",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def td_screenshot(params: ScreenshotInput, ctx: Context) -> str:
    """Capture a TOP node as a PNG image.

    Returns the image as base64-encoded data. Point this at any TOP node
    (render TOPs, null TOPs, composite TOPs, etc.) to see its current output.

    Args:
        params: path (str) — path to a TOP node

    Returns:
        str: JSON with success, width, height, format, data_base64, and size_bytes.
             The data_base64 field contains the raw PNG image as a base64 string.
    """
    try:
        client = _get_client(ctx)
        data = await client.request("screenshot", params.model_dump())
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


# ═══════════════════════════════════════════════════════════════
# TOOLS — CHOP / SOP Data
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="td_chop_data",
    annotations={
        "title": "Read CHOP Channel Data",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def td_chop_data(params: CHOPDataInput, ctx: Context) -> str:
    """Read channel values from a CHOP node.

    Returns sample values for each channel. Large datasets are automatically
    downsampled to ~1000 samples. Use the 'channels' filter for specific channels
    and 'range' for sample subsets.

    Args:
        params: path (str), channels (optional list), range (optional [start, end])

    Returns:
        str: JSON with numChans, numSamples, rate, and channels dict
             (each channel has 'values' array and 'downsampled' flag).
    """
    try:
        client = _get_client(ctx)
        data = await client.request("chop/data", params.model_dump(exclude_none=True))
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="td_sop_data",
    annotations={
        "title": "Read SOP Geometry Data",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def td_sop_data(params: SOPDataInput, ctx: Context) -> str:
    """Read geometry data from a SOP node: point positions and primitive info.

    Useful for inspecting geometry, debugging SOP networks, or extracting
    point cloud data. Limited to 'limit' points/prims by default.

    Args:
        params: path (str), include_points (bool), include_prims (bool), limit (int)

    Returns:
        str: JSON with numPoints, numPrims, numVertices, and optional
             points array (x, y, z per point) and prims array.
    """
    try:
        client = _get_client(ctx)
        data = await client.request("sop/data", params.model_dump())
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


# ═══════════════════════════════════════════════════════════════
# TOOLS — Performance / Cooking
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="td_cooking_info",
    annotations={
        "title": "Get Cooking/Performance Info",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def td_cooking_info(params: CookingInfoInput, ctx: Context) -> str:
    """Get cooking performance data: cook times per node, sorted by slowest.

    Use this to identify performance bottlenecks in a TD network.
    Set recurse=True to scan an entire sub-network.

    Args:
        params: path (str), recurse (bool), sort_by (str), limit (int)

    Returns:
        str: JSON with fps, realTime, frame, and nodes array sorted by cook time.
    """
    try:
        client = _get_client(ctx)
        data = await client.request("cooking", params.model_dump())
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


# ═══════════════════════════════════════════════════════════════
# TOOLS — Search
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="td_search_nodes",
    annotations={
        "title": "Search Nodes",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def td_search_nodes(params: SearchNodesInput, ctx: Context) -> str:
    """Search for nodes by name, type, or family (case-insensitive, substring match).

    Recursively searches from the given path. Use search_type to narrow:
    - 'name': match node names
    - 'type': match operator types (e.g. 'noiseTOP')
    - 'family': match families (e.g. 'TOP', 'CHOP')
    - 'all': match any field

    Args:
        params: query (str), path (str), search_type (str), limit (int)

    Returns:
        str: JSON with matching nodes array.
    """
    try:
        client = _get_client(ctx)
        data = await client.request("search", params.model_dump())
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


# ═══════════════════════════════════════════════════════════════
# TOOLS — Error Checking
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="td_get_errors",
    annotations={
        "title": "Check Node Errors",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def td_get_errors(params: GetErrorsInput, ctx: Context) -> str:
    """Check for errors and warnings on a node, optionally recursing into children.

    Use this to diagnose broken networks or verify a node chain is healthy.

    Args:
        params: path (str, default '/'), recurse (bool, default True)

    Returns:
        str: JSON with issues array (each has path, errors, warnings).
    """
    try:
        client = _get_client(ctx)
        data = await client.request("node/errors", params.model_dump())
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


# ═══════════════════════════════════════════════════════════════
# TOOLS — Timeline Control
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="td_timeline",
    annotations={
        "title": "Get Timeline State",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def td_timeline(ctx: Context) -> str:
    """Get the current timeline/playback state: frame, seconds, playing, FPS, range.

    Returns:
        str: JSON with frame, seconds, playing (bool), fps, start, end.
    """
    try:
        client = _get_client(ctx)
        data = await client.request("timeline")
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="td_timeline_set",
    annotations={
        "title": "Control Timeline",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def td_timeline_set(params: TimelineSetInput, ctx: Context) -> str:
    """Control timeline playback: play, pause, jump to frame, or set FPS.

    Args:
        params: action ('play', 'pause', or 'frame'), frame (int), fps (float)

    Returns:
        str: JSON with success and updated state.
    """
    try:
        client = _get_client(ctx)
        data = await client.request("timeline/set", params.model_dump(exclude_none=True))
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


# ═══════════════════════════════════════════════════════════════
# TOOLS — Pulse Parameter
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="td_pulse_param",
    annotations={
        "title": "Pulse Parameter",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def td_pulse_param(params: PulseParamInput, ctx: Context) -> str:
    """Pulse a pulse-type parameter (like 'Cook', 'Reset', 'Resetpulse', etc.).

    Many TD operators have pulse parameters that trigger one-shot actions.

    Args:
        params: path (str), param (str) — the parameter name to pulse

    Returns:
        str: JSON with success flag.
    """
    try:
        client = _get_client(ctx)
        data = await client.request("pulse", params.model_dump())
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


# ═══════════════════════════════════════════════════════════════
# TOOLS — Python Help / Introspection
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="td_python_help",
    annotations={
        "title": "Get TD Python Help",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def td_python_help(params: PythonHelpInput, ctx: Context) -> str:
    """Get Python help() documentation for a TouchDesigner module, class, or function.

    Use targets like: 'td', 'td.OP', 'td.TOP', 'td.CHOP', 'tdu', 'td.Par', etc.

    Args:
        params: target (str) — Python object path to get help for

    Returns:
        str: JSON with the help text output (may be truncated for large docs).
    """
    try:
        client = _get_client(ctx)
        data = await client.request("python/help", params.model_dump())
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="td_python_classes",
    annotations={
        "title": "List TD Python Classes",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def td_python_classes(ctx: Context) -> str:
    """List all available TouchDesigner Python classes and modules from the 'td' module.

    Returns:
        str: JSON with module name, list of class/attribute names, and count.
    """
    try:
        client = _get_client(ctx)
        data = await client.request("python/classes")
        return json.dumps(data, indent=2)
    except Exception as e:
        return _handle_error(e)


# ═══════════════════════════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════════════════════════

def main():
    """Run the MCP server with stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
