"""
Pydantic Input Models for TouchDesigner MCP Tools
==================================================
All input validation, constraints, and descriptions for every tool.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum


class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


# ─────────────────────────────────────────────────────────────
# Environment / Info
# ─────────────────────────────────────────────────────────────

class EmptyInput(BaseModel):
    """No input required."""
    model_config = ConfigDict(extra='forbid')


# ─────────────────────────────────────────────────────────────
# Node Navigation & Inspection
# ─────────────────────────────────────────────────────────────

class GetNodesInput(BaseModel):
    """Input for listing child nodes at a path."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    path: str = Field(
        default="/",
        description="Absolute path to a COMP node whose children to list (e.g. '/', '/project1', '/project1/myComp')"
    )
    family: Optional[str] = Field(
        default=None,
        description="Filter by operator family: TOP, CHOP, SOP, DAT, COMP, MAT, or PANEL"
    )
    type: Optional[str] = Field(
        default=None,
        description="Filter by specific operator type (e.g. 'noiseTOP', 'waveCHOP', 'textDAT')"
    )
    include_params: bool = Field(
        default=False,
        description="If true, include all parameters for each node (slower for large networks)"
    )
    limit: int = Field(default=100, ge=1, le=500, description="Max number of nodes to return")
    offset: int = Field(default=0, ge=0, description="Pagination offset")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON, description="Output format")


class NodePathInput(BaseModel):
    """Input requiring a single node path."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    path: str = Field(
        ...,
        description="Absolute path to the node (e.g. '/project1/noise1', '/project1/geo1/sphere1')",
        min_length=1,
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON, description="Output format")


class GetParamsInput(BaseModel):
    """Input for getting node parameters."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    path: str = Field(..., description="Absolute node path", min_length=1)
    page: Optional[str] = Field(default=None, description="Filter by parameter page name")
    names: Optional[List[str]] = Field(default=None, description="Filter to specific parameter names")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON, description="Output format")


class SetParamsInput(BaseModel):
    """Input for setting node parameters (static values or live expressions)."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    path: str = Field(..., description="Absolute node path", min_length=1)
    params: Dict[str, Any] = Field(
        ...,
        description=(
            "Dictionary of parameter names to values. Supports three modes:\n"
            "• Static value (plain): {'seed': 42, 'colorr': 1.0}\n"
            "• Expression (reactive, updates every frame): {'seed': {'expr': 'absTime.seconds * 10'}, 'tx': {'expr': \"op('noise1')['chan1']\"}}\n"
            "• Explicit static: {'seed': {'val': 42}}\n\n"
            "Expressions make networks ALIVE — use them for anything that should move, react, or change over time."
        ),
        min_length=1,
    )


# ─────────────────────────────────────────────────────────────
# Node Creation / Deletion / Copy / Rename
# ─────────────────────────────────────────────────────────────

class CreateNodeInput(BaseModel):
    """Input for creating a new node."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    parent_path: str = Field(
        default="/project1",
        description="Path to the parent COMP where the node will be created"
    )
    node_type: str = Field(
        ...,
        description=(
            "TouchDesigner operator type to create. Examples: "
            "TOPs: 'noiseTOP', 'levelTOP', 'nullTOP', 'compositeTOP', 'feedbackTOP', 'moviefileinTOP' | "
            "CHOPs: 'waveCHOP', 'noiseCHOP', 'nullCHOP', 'mathCHOP', 'constantCHOP', 'selectCHOP' | "
            "SOPs: 'sphereSOP', 'boxSOP', 'gridSOP', 'lineSOP', 'nullSOP', 'transformSOP', 'noiseSOP' | "
            "DATs: 'textDAT', 'tableDAT', 'scriptDAT', 'nullDAT', 'selectDAT', 'chopexecDAT' | "
            "COMPs: 'baseCOMP', 'containerCOMP', 'geometryCOMP', 'cameraCOMP', 'lightCOMP' | "
            "MATs: 'pbrMAT', 'phongMAT', 'wireframeMAT', 'constMAT'"
        ),
        min_length=1,
    )
    name: Optional[str] = Field(
        default=None,
        description="Custom name for the new node. If None, TD assigns a default name."
    )
    nodeX: Optional[int] = Field(
        default=None,
        description="Horizontal position in the network editor (pixels). Use multiples of 200 for clean spacing between nodes."
    )
    nodeY: Optional[int] = Field(
        default=None,
        description="Vertical position in the network editor (pixels). Use multiples of 200 for clean spacing between rows."
    )

    @field_validator('node_type')
    @classmethod
    def validate_node_type(cls, v: str) -> str:
        families = ('TOP', 'CHOP', 'SOP', 'DAT', 'COMP', 'MAT')
        if not any(v.upper().endswith(f) for f in families):
            # Allow it but warn — TD will reject invalid types anyway
            pass
        return v


class DeleteNodeInput(BaseModel):
    """Input for deleting a node."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    path: str = Field(..., description="Absolute path of the node to delete", min_length=1)


class CopyNodeInput(BaseModel):
    """Input for copying/duplicating a node."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    source_path: str = Field(..., description="Path of the node to copy", min_length=1)
    dest_parent: Optional[str] = Field(
        default=None,
        description="Path of the destination parent COMP. If None, copies into same parent."
    )
    new_name: Optional[str] = Field(default=None, description="Name for the copy")


class RenameNodeInput(BaseModel):
    """Input for renaming a node."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    path: str = Field(..., description="Current absolute path of the node", min_length=1)
    new_name: str = Field(..., description="New name for the node", min_length=1, max_length=100)


# ─────────────────────────────────────────────────────────────
# Connections / Wiring
# ─────────────────────────────────────────────────────────────

class ConnectNodesInput(BaseModel):
    """Input for connecting two nodes."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    source_path: str = Field(..., description="Path of the source (output) node", min_length=1)
    target_path: str = Field(..., description="Path of the target (input) node", min_length=1)
    source_index: int = Field(
        default=0, ge=0,
        description="Output connector index on the source node (0 = first output)"
    )
    target_index: int = Field(
        default=0, ge=0,
        description="Input connector index on the target node (0 = first input)"
    )


class DisconnectInput(BaseModel):
    """Input for disconnecting a node connector."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    path: str = Field(..., description="Path of the node to disconnect", min_length=1)
    connector_type: str = Field(
        default="input",
        description="Which connector: 'input' or 'output'"
    )
    index: int = Field(default=0, ge=0, description="Connector index to disconnect")

    @field_validator('connector_type')
    @classmethod
    def validate_connector_type(cls, v: str) -> str:
        if v not in ('input', 'output'):
            raise ValueError("connector_type must be 'input' or 'output'")
        return v


# ─────────────────────────────────────────────────────────────
# DAT Content
# ─────────────────────────────────────────────────────────────

class GetContentInput(BaseModel):
    """Input for reading DAT text/table content."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    path: str = Field(..., description="Path to a DAT node", min_length=1)


class SetContentInput(BaseModel):
    """Input for writing DAT text/table content."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    path: str = Field(..., description="Path to a DAT node", min_length=1)
    text: Optional[str] = Field(
        default=None,
        description="Text content to write (for Text DATs, Script DATs, etc.)"
    )
    table: Optional[List[List[str]]] = Field(
        default=None,
        description="Table content as 2D array of strings (for Table DATs)"
    )


# ─────────────────────────────────────────────────────────────
# Python Execution
# ─────────────────────────────────────────────────────────────

class ExecPythonInput(BaseModel):
    """Input for executing Python code inside TouchDesigner."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    code: str = Field(
        ...,
        description=(
            "Python code to execute in TouchDesigner's Python environment. "
            "Has access to: op(), ops(), project, app, absTime, me, parent(), mod, ui, tdu. "
            "Set __result__ = <value> to return a value to the caller. "
            "Example: '__result__ = op(\"/project1/noise1\").par.type.eval()'"
        ),
        min_length=1,
        max_length=50000,
    )


# ─────────────────────────────────────────────────────────────
# Screenshot / Visual
# ─────────────────────────────────────────────────────────────

class ScreenshotInput(BaseModel):
    """Input for capturing a TOP node as an image."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    path: str = Field(
        ...,
        description="Path to a TOP node to capture as an image (e.g. '/project1/null1', '/project1/render1')",
        min_length=1,
    )


# ─────────────────────────────────────────────────────────────
# CHOP / SOP Data
# ─────────────────────────────────────────────────────────────

class CHOPDataInput(BaseModel):
    """Input for reading CHOP channel data."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    path: str = Field(..., description="Path to a CHOP node", min_length=1)
    channels: Optional[List[str]] = Field(
        default=None,
        description="List of channel names to read. If None, reads all channels."
    )
    range: Optional[List[int]] = Field(
        default=None,
        description="Sample range [start, end] to read. If None, reads all samples.",
        min_length=2, max_length=2,
    )


class SOPDataInput(BaseModel):
    """Input for reading SOP geometry data."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    path: str = Field(..., description="Path to a SOP node", min_length=1)
    include_points: bool = Field(default=True, description="Include point position data")
    include_prims: bool = Field(default=False, description="Include primitive data")
    limit: int = Field(default=500, ge=1, le=10000, description="Max points/prims to return")


# ─────────────────────────────────────────────────────────────
# Cooking / Performance
# ─────────────────────────────────────────────────────────────

class CookingInfoInput(BaseModel):
    """Input for getting cooking/performance info."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    path: str = Field(default="/", description="Root path to inspect")
    recurse: bool = Field(default=False, description="Recursively inspect children")
    sort_by: str = Field(default="cookTime", description="Sort by: 'cookTime' or 'cpuCookTime'")
    limit: int = Field(default=20, ge=1, le=100, description="Max nodes to return")


# ─────────────────────────────────────────────────────────────
# Search
# ─────────────────────────────────────────────────────────────

class SearchNodesInput(BaseModel):
    """Input for searching nodes."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    query: str = Field(..., description="Search string (case-insensitive)", min_length=1)
    path: str = Field(default="/", description="Root path to search from")
    search_type: str = Field(
        default="all",
        description="What to search: 'name', 'type', 'family', or 'all'"
    )
    limit: int = Field(default=50, ge=1, le=200, description="Max results")

    @field_validator('search_type')
    @classmethod
    def validate_search_type(cls, v: str) -> str:
        if v not in ('name', 'type', 'family', 'all'):
            raise ValueError("search_type must be 'name', 'type', 'family', or 'all'")
        return v


# ─────────────────────────────────────────────────────────────
# Python Help / Introspection
# ─────────────────────────────────────────────────────────────

class PythonHelpInput(BaseModel):
    """Input for getting Python help documentation."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    target: str = Field(
        ...,
        description="Python object/class to get help for (e.g. 'td', 'td.OP', 'tdu', 'td.TOP')",
        min_length=1,
    )


# ─────────────────────────────────────────────────────────────
# Timeline
# ─────────────────────────────────────────────────────────────

class TimelineSetInput(BaseModel):
    """Input for controlling timeline playback."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    action: Optional[str] = Field(
        default=None,
        description="Timeline action: 'play', 'pause', or 'frame' (set specific frame)"
    )
    frame: Optional[int] = Field(default=None, ge=0, description="Frame number to jump to (when action='frame')")
    fps: Optional[float] = Field(default=None, gt=0, le=240, description="Set cook rate / FPS")


# ─────────────────────────────────────────────────────────────
# Pulse Parameter
# ─────────────────────────────────────────────────────────────

class PulseParamInput(BaseModel):
    """Input for pulsing a pulse-type parameter."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    path: str = Field(..., description="Node path", min_length=1)
    param: str = Field(..., description="Parameter name to pulse", min_length=1)


# ─────────────────────────────────────────────────────────────
# Error Checking
# ─────────────────────────────────────────────────────────────

class GetErrorsInput(BaseModel):
    """Input for checking node errors."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    path: str = Field(default="/", description="Node path to check")
    recurse: bool = Field(default=True, description="Recursively check children")

