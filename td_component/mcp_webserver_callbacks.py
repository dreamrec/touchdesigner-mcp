"""
TouchDesigner MCP WebServer DAT Callbacks
==========================================
Paste this into the callbacks DAT attached to your WebServer DAT.
This is the TD-side router that receives HTTP requests from the
FastMCP server and executes operations using the TD Python API.

Setup:
  1. Create a Base COMP named 'mcp_server'
  2. Inside it, create a WebServer DAT (port 9981, Active=On)
  3. Attach this script as the callbacks DAT
  4. Optionally add a Movie File Out TOP named 'mcp_screenshot' for captures

Compatible with TouchDesigner 2025.30000+
"""

import json
import traceback
import sys
import os
import base64
import time

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

API_VERSION = "1.0.0"
SCREENSHOT_TEMP_PATH = "/tmp/td_mcp_screenshot.png"

# ─────────────────────────────────────────────────────────────
# Main HTTP Router
# ─────────────────────────────────────────────────────────────

def onHTTPRequest(webServerDAT, request, response):
    """
    Main entry point for all MCP server requests.
    Routes to handler functions based on URI path.
    """
    uri = request.get('uri', '/')
    method = request.get('method', 'GET')

    # Parse JSON body
    body = {}
    raw_data = request.get('data', None)
    if raw_data:
        try:
            if isinstance(raw_data, bytes):
                body = json.loads(raw_data.decode('utf-8'))
            elif isinstance(raw_data, str):
                body = json.loads(raw_data)
        except (json.JSONDecodeError, UnicodeDecodeError):
            body = {}

    # CORS headers for local development
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

    # Handle OPTIONS preflight
    if method == 'OPTIONS':
        response['statusCode'] = 204
        response['statusReason'] = 'No Content'
        response['data'] = ''
        return response

    try:
        # ── Route table ──
        routes = {
            '/api/health':              handle_health,
            '/api/info':                handle_info,
            '/api/nodes':               handle_get_nodes,
            '/api/node/detail':         handle_get_node_detail,
            '/api/node/params':         handle_get_params,
            '/api/node/params/set':     handle_set_params,
            '/api/node/create':         handle_create_node,
            '/api/node/delete':         handle_delete_node,
            '/api/node/connect':        handle_connect_nodes,
            '/api/node/disconnect':     handle_disconnect_nodes,
            '/api/node/connections':    handle_get_connections,
            '/api/node/errors':         handle_get_errors,
            '/api/node/content':        handle_get_content,
            '/api/node/content/set':    handle_set_content,
            '/api/node/copy':           handle_copy_node,
            '/api/node/rename':         handle_rename_node,
            '/api/exec':                handle_exec_python,
            '/api/screenshot':          handle_screenshot,
            '/api/chop/data':           handle_chop_data,
            '/api/sop/data':            handle_sop_data,
            '/api/cooking':             handle_cooking_info,
            '/api/search':              handle_search_nodes,
            '/api/families':            handle_list_families,
            '/api/python/help':         handle_python_help,
            '/api/python/classes':      handle_python_classes,
            '/api/timeline':            handle_timeline,
            '/api/timeline/set':        handle_timeline_set,
            '/api/pulse':               handle_pulse_param,
        }

        handler = routes.get(uri)
        if handler:
            result = handler(body)
        else:
            result = {'error': f'Unknown endpoint: {uri}', 'available': list(routes.keys())}
            response['statusCode'] = 404
            response['statusReason'] = 'Not Found'
            _send_json(response, result)
            return response

        response['statusCode'] = 200
        response['statusReason'] = 'OK'
        _send_json(response, result)

    except Exception as e:
        error_result = {
            'error': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        }
        response['statusCode'] = 500
        response['statusReason'] = 'Internal Server Error'
        _send_json(response, error_result)

    return response


def _send_json(response, data):
    """Helper to serialize and set JSON response."""
    response['data'] = json.dumps(data, default=str).encode('utf-8')
    response['content-type'] = 'application/json'


def _serialize_op(node, include_params=False):
    """Serialize a TD operator to a dict."""
    info = {
        'name': node.name,
        'path': node.path,
        'type': node.type,
        'family': node.family,
        'label': getattr(node, 'label', ''),
        'nodeX': node.nodeX,
        'nodeY': node.nodeY,
        'isCOMP': node.isCOMP,
        'isTOP': node.isTOP,
        'isCHOP': node.isCHOP,
        'isSOP': node.isSOP,
        'isDAT': node.isDAT,
        'isMAT': node.isMAT,
        'isPOP': getattr(node, 'isPOP', False),
        'bypass': node.bypass,
        'lock': node.lock,
        'display': node.display if hasattr(node, 'display') else False,
        'render': node.render if hasattr(node, 'render') else False,
        'errors': node.errors(recurse=False) if hasattr(node, 'errors') else '',
        'warnings': node.warnings(recurse=False) if hasattr(node, 'warnings') else '',
    }
    if include_params:
        info['parameters'] = _serialize_params(node)
    return info


def _serialize_params(node):
    """Serialize all parameters of a node."""
    params = {}
    for p in node.pars():
        try:
            info = {
                'value': p.eval(),
                'default': p.default,
                'label': p.label,
                'page': p.page.name if p.page else '',
                'style': p.style,
                'min': p.min if hasattr(p, 'min') else None,
                'max': p.max if hasattr(p, 'max') else None,
                'readOnly': p.readOnly,
                'isPulse': p.isPulse,
                'isMomentary': p.isMomentary,
                'isToggle': p.isToggle,
                'isMenu': p.isMenu,
                'menuNames': list(p.menuNames) if p.isMenu else [],
                'menuLabels': list(p.menuLabels) if p.isMenu else [],
            }
            # Include expression info — this tells the AI whether a param
            # is static or driven by an expression/export
            try:
                info['expr'] = p.expr if p.expr else ''
                info['mode'] = str(p.mode)
            except:
                info['expr'] = ''
                info['mode'] = 'CONSTANT'
            params[p.name] = info
        except Exception:
            params[p.name] = {'value': str(p), 'error': 'Could not fully serialize'}
    return params


# ─────────────────────────────────────────────────────────────
# Handlers
# ─────────────────────────────────────────────────────────────

def handle_health(body):
    """Health check endpoint."""
    return {
        'status': 'ok',
        'api_version': API_VERSION,
        'timestamp': time.time(),
    }


def handle_info(body):
    """Get TouchDesigner environment info."""
    return {
        'version': app.version,
        'build': app.build,
        'osName': app.osName,
        'osVersion': app.osVersion,
        'product': app.product,
        'project_name': project.name,
        'project_folder': project.folder,
        'fps': project.cookRate,
        'realTime': project.realTime,
        'frame': absTime.frame,
        'seconds': absTime.seconds,
        'timeline_start': project.cookRange[0] if hasattr(project, 'cookRange') else 1,
        'timeline_end': project.cookRange[1] if hasattr(project, 'cookRange') else 600,
        'api_version': API_VERSION,
    }


def handle_get_nodes(body):
    """List children of a path, with optional filtering."""
    path = body.get('path', '/')
    family_filter = body.get('family', None)
    type_filter = body.get('type', None)
    depth = body.get('depth', 1)
    include_params = body.get('include_params', False)
    limit = body.get('limit', 100)
    offset = body.get('offset', 0)

    target = op(path)
    if target is None:
        return {'error': f'Node not found: {path}'}

    if not target.isCOMP:
        return {'error': f'Node is not a COMP (cannot have children): {path}', 'node_type': target.type}

    children = target.children

    # Apply filters
    if family_filter:
        family_filter = family_filter.upper()
        children = [c for c in children if c.family == family_filter]
    if type_filter:
        children = [c for c in children if c.type == type_filter]

    total = len(children)
    children = children[offset:offset + limit]

    nodes = [_serialize_op(c, include_params=include_params) for c in children]

    return {
        'path': path,
        'total': total,
        'count': len(nodes),
        'offset': offset,
        'has_more': total > offset + len(nodes),
        'nodes': nodes,
    }


def handle_get_node_detail(body):
    """Get detailed info about a single node."""
    path = body.get('path')
    if not path:
        return {'error': 'Missing required field: path'}

    node = op(path)
    if node is None:
        return {'error': f'Node not found: {path}'}

    detail = _serialize_op(node, include_params=True)

    # Add connection info
    detail['inputs'] = []
    for conn in node.inputConnectors:
        for c in conn.connections:
            detail['inputs'].append({
                'from': c.owner.path,
                'from_index': c.index,
                'to_index': conn.index,
            })

    detail['outputs'] = []
    for conn in node.outputConnectors:
        for c in conn.connections:
            detail['outputs'].append({
                'to': c.owner.path,
                'to_index': c.index,
                'from_index': conn.index,
            })

    # Children count if COMP
    if node.isCOMP:
        detail['children_count'] = len(node.children)
        detail['child_names'] = [c.name for c in node.children[:50]]

    return detail


def handle_get_params(body):
    """Get parameters for a specific node."""
    path = body.get('path')
    if not path:
        return {'error': 'Missing required field: path'}

    node = op(path)
    if node is None:
        return {'error': f'Node not found: {path}'}

    page_filter = body.get('page', None)
    name_filter = body.get('names', None)

    params = {}
    for p in node.pars():
        if page_filter and p.page and p.page.name != page_filter:
            continue
        if name_filter and p.name not in name_filter:
            continue
        try:
            info = {
                'value': p.eval(),
                'default': p.default,
                'label': p.label,
                'page': p.page.name if p.page else '',
                'style': p.style,
                'readOnly': p.readOnly,
                'isPulse': p.isPulse,
                'isMenu': p.isMenu,
                'menuNames': list(p.menuNames) if p.isMenu else [],
            }
            # Include expression info
            try:
                info['expr'] = p.expr if p.expr else ''
                info['mode'] = str(p.mode)
            except:
                info['expr'] = ''
                info['mode'] = 'CONSTANT'
            params[p.name] = info
        except Exception:
            params[p.name] = {'value': str(p), 'error': 'Could not serialize'}

    return {'path': path, 'type': node.type, 'parameters': params}


def handle_set_params(body):
    """Set one or more parameters on a node.

    Each param value can be:
      - A plain value (int, float, str, bool) → sets p.val (static constant)
      - A dict with 'expr' key → sets p.expr (Python expression that updates every frame)
        Example: {"seed": {"expr": "absTime.seconds * 10"}}
        Example: {"tx": {"expr": "op('noise1')['chan1']"}}
      - A dict with 'val' key → explicitly sets p.val (same as plain value)

    Expressions make networks REACTIVE — the parameter updates every frame.
    Without expressions, values are static snapshots.
    """
    path = body.get('path')
    params = body.get('params', {})

    if not path:
        return {'error': 'Missing required field: path'}
    if not params:
        return {'error': 'Missing required field: params'}

    node = op(path)
    if node is None:
        return {'error': f'Node not found: {path}'}

    results = {}
    for name, value in params.items():
        try:
            p = getattr(node.par, name, None)
            if p is None:
                results[name] = {'success': False, 'error': f'Parameter not found: {name}'}
                continue
            if p.readOnly:
                results[name] = {'success': False, 'error': f'Parameter is read-only: {name}'}
                continue

            # Expression mode: {"param": {"expr": "absTime.seconds * 10"}}
            if isinstance(value, dict) and 'expr' in value:
                p.expr = value['expr']
                results[name] = {
                    'success': True,
                    'mode': 'expression',
                    'expr': value['expr'],
                    'current_value': p.eval(),
                }
            # Explicit val mode: {"param": {"val": 42}}
            elif isinstance(value, dict) and 'val' in value:
                p.val = value['val']
                results[name] = {'success': True, 'mode': 'constant', 'new_value': p.eval()}
            # Plain value (backwards compatible)
            else:
                p.val = value
                results[name] = {'success': True, 'mode': 'constant', 'new_value': p.eval()}
        except Exception as e:
            results[name] = {'success': False, 'error': str(e)}

    return {'path': path, 'results': results}


def handle_create_node(body):
    """Create a new node with optional positioning."""
    parent_path = body.get('parent_path', '/')
    node_type = body.get('node_type')
    name = body.get('name', None)
    node_x = body.get('nodeX', None)
    node_y = body.get('nodeY', None)

    if not node_type:
        return {'error': 'Missing required field: node_type'}

    parent_node = op(parent_path)
    if parent_node is None:
        return {'error': f'Parent node not found: {parent_path}'}

    if not parent_node.isCOMP:
        return {'error': f'Parent is not a COMP: {parent_path}'}

    try:
        new_node = parent_node.create(node_type, name)

        # Set position if provided — keeps networks readable
        if node_x is not None:
            new_node.nodeX = int(node_x)
        if node_y is not None:
            new_node.nodeY = int(node_y)

        return {
            'success': True,
            'node': _serialize_op(new_node),
        }
    except Exception as e:
        return {'error': f'Failed to create node: {str(e)}', 'node_type': node_type}


def handle_delete_node(body):
    """Delete a node by path."""
    path = body.get('path')
    if not path:
        return {'error': 'Missing required field: path'}

    node = op(path)
    if node is None:
        return {'error': f'Node not found: {path}'}

    node_info = {'name': node.name, 'path': node.path, 'type': node.type}

    try:
        node.destroy()
        return {'success': True, 'deleted': node_info}
    except Exception as e:
        return {'error': f'Failed to delete node: {str(e)}'}


def handle_connect_nodes(body):
    """Connect output of one node to input of another."""
    source_path = body.get('source_path')
    target_path = body.get('target_path')
    source_index = body.get('source_index', 0)
    target_index = body.get('target_index', 0)

    if not source_path or not target_path:
        return {'error': 'Missing required fields: source_path and target_path'}

    source = op(source_path)
    target = op(target_path)

    if source is None:
        return {'error': f'Source node not found: {source_path}'}
    if target is None:
        return {'error': f'Target node not found: {target_path}'}

    try:
        source.outputConnectors[source_index].connect(target.inputConnectors[target_index])
        return {
            'success': True,
            'connection': {
                'source': source.path,
                'source_index': source_index,
                'target': target.path,
                'target_index': target_index,
            }
        }
    except Exception as e:
        return {'error': f'Failed to connect: {str(e)}'}


def handle_disconnect_nodes(body):
    """Disconnect a node's input or output."""
    path = body.get('path')
    connector_type = body.get('connector_type', 'input')  # 'input' or 'output'
    index = body.get('index', 0)

    if not path:
        return {'error': 'Missing required field: path'}

    node = op(path)
    if node is None:
        return {'error': f'Node not found: {path}'}

    try:
        if connector_type == 'input':
            node.inputConnectors[index].disconnect()
        else:
            node.outputConnectors[index].disconnect()
        return {'success': True, 'path': path, 'connector_type': connector_type, 'index': index}
    except Exception as e:
        return {'error': f'Failed to disconnect: {str(e)}'}


def handle_get_connections(body):
    """Get all connections for a node."""
    path = body.get('path')
    if not path:
        return {'error': 'Missing required field: path'}

    node = op(path)
    if node is None:
        return {'error': f'Node not found: {path}'}

    inputs = []
    for conn in node.inputConnectors:
        for c in conn.connections:
            inputs.append({
                'from_path': c.owner.path,
                'from_index': c.index,
                'to_index': conn.index,
            })

    outputs = []
    for conn in node.outputConnectors:
        for c in conn.connections:
            outputs.append({
                'to_path': c.owner.path,
                'to_index': c.index,
                'from_index': conn.index,
            })

    return {'path': path, 'inputs': inputs, 'outputs': outputs}


def handle_get_errors(body):
    """Get errors/warnings for a node, optionally recursive."""
    path = body.get('path', '/')
    recurse = body.get('recurse', True)

    node = op(path)
    if node is None:
        return {'error': f'Node not found: {path}'}

    results = []

    def collect_errors(n):
        errs = n.errors(recurse=False) if hasattr(n, 'errors') else ''
        warns = n.warnings(recurse=False) if hasattr(n, 'warnings') else ''
        if errs or warns:
            results.append({
                'path': n.path,
                'name': n.name,
                'type': n.type,
                'errors': errs,
                'warnings': warns,
            })
        if recurse and n.isCOMP:
            for child in n.children:
                collect_errors(child)

    collect_errors(node)
    return {'path': path, 'recurse': recurse, 'count': len(results), 'issues': results}


def handle_get_content(body):
    """Get text/table content from a DAT."""
    path = body.get('path')
    if not path:
        return {'error': 'Missing required field: path'}

    node = op(path)
    if node is None:
        return {'error': f'Node not found: {path}'}

    if not node.isDAT:
        return {'error': f'Node is not a DAT: {path} (type: {node.type})'}

    try:
        # Try table format first
        if hasattr(node, 'numRows') and node.numRows > 0:
            rows = []
            for r in range(node.numRows):
                row = []
                for c in range(node.numCols):
                    row.append(node[r, c].val)
                rows.append(row)
            return {
                'path': path,
                'format': 'table',
                'numRows': node.numRows,
                'numCols': node.numCols,
                'data': rows,
            }
        else:
            return {
                'path': path,
                'format': 'text',
                'text': node.text,
            }
    except Exception:
        return {
            'path': path,
            'format': 'text',
            'text': node.text if hasattr(node, 'text') else '',
        }


def handle_set_content(body):
    """Set text/table content on a DAT."""
    path = body.get('path')
    text = body.get('text', None)
    table = body.get('table', None)

    if not path:
        return {'error': 'Missing required field: path'}

    node = op(path)
    if node is None:
        return {'error': f'Node not found: {path}'}

    if not node.isDAT:
        return {'error': f'Node is not a DAT: {path}'}

    try:
        if text is not None:
            node.text = text
            return {'success': True, 'path': path, 'format': 'text', 'length': len(text)}
        elif table is not None:
            node.clear()
            for r, row in enumerate(table):
                for c, val in enumerate(row):
                    node[r, c] = val
            return {'success': True, 'path': path, 'format': 'table', 'rows': len(table)}
        else:
            return {'error': 'Provide either "text" or "table" field'}
    except Exception as e:
        return {'error': f'Failed to set content: {str(e)}'}


def handle_copy_node(body):
    """Copy/duplicate a node."""
    source_path = body.get('source_path')
    dest_parent = body.get('dest_parent', None)
    new_name = body.get('new_name', None)

    if not source_path:
        return {'error': 'Missing required field: source_path'}

    source = op(source_path)
    if source is None:
        return {'error': f'Source node not found: {source_path}'}

    parent = op(dest_parent) if dest_parent else source.parent()
    if parent is None:
        return {'error': f'Destination parent not found: {dest_parent}'}

    try:
        new_node = parent.copy(source, name=new_name)
        return {'success': True, 'node': _serialize_op(new_node)}
    except Exception as e:
        return {'error': f'Failed to copy node: {str(e)}'}


def handle_rename_node(body):
    """Rename a node."""
    path = body.get('path')
    new_name = body.get('new_name')

    if not path or not new_name:
        return {'error': 'Missing required fields: path and new_name'}

    node = op(path)
    if node is None:
        return {'error': f'Node not found: {path}'}

    old_name = node.name
    try:
        node.name = new_name
        return {'success': True, 'old_name': old_name, 'new_name': node.name, 'new_path': node.path}
    except Exception as e:
        return {'error': f'Failed to rename: {str(e)}'}


def handle_exec_python(body):
    """Execute arbitrary Python code inside TouchDesigner."""
    code = body.get('code')
    if not code:
        return {'error': 'Missing required field: code'}

    # Capture stdout
    import io
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    captured_out = io.StringIO()
    captured_err = io.StringIO()

    result_value = None
    try:
        sys.stdout = captured_out
        sys.stderr = captured_err

        # Try exec first, fall back to eval for expressions
        try:
            exec_globals = {'op': op, 'ops': ops, 'project': project, 'app': app,
                          'absTime': absTime, 'me': me, 'parent': parent, 'mod': mod,
                          'ui': ui, 'tdu': tdu}
            exec(code, exec_globals)
            # Check if there's a __result__ variable
            result_value = exec_globals.get('__result__', None)
        except SyntaxError:
            # Might be a simple expression
            result_value = eval(code)
    except Exception as e:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        return {
            'error': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc(),
            'stdout': captured_out.getvalue(),
            'stderr': captured_err.getvalue(),
        }
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    return {
        'success': True,
        'result': str(result_value) if result_value is not None else None,
        'stdout': captured_out.getvalue(),
        'stderr': captured_err.getvalue(),
    }


def handle_screenshot(body):
    """Capture a TOP as a PNG image and return base64."""
    path = body.get('path', None)

    try:
        if path:
            target = op(path)
            if target is None:
                return {'error': f'Node not found: {path}'}
            if not target.isTOP:
                return {'error': f'Node is not a TOP: {path} (type: {target.type})'}
        else:
            # Try to find the first render or output TOP
            return {'error': 'Provide path to a TOP node to screenshot'}

        # Use saveByteArray for in-memory capture
        img_bytes = target.saveByteArray('.png')
        img_b64 = base64.b64encode(bytes(img_bytes)).decode('ascii')

        return {
            'success': True,
            'path': target.path,
            'width': target.width,
            'height': target.height,
            'format': 'png',
            'data_base64': img_b64,
            'size_bytes': len(img_bytes),
        }
    except Exception as e:
        # Fallback: try file-based save
        try:
            target.save(SCREENSHOT_TEMP_PATH)
            with open(SCREENSHOT_TEMP_PATH, 'rb') as f:
                img_bytes = f.read()
            img_b64 = base64.b64encode(img_bytes).decode('ascii')
            return {
                'success': True,
                'path': target.path,
                'format': 'png',
                'data_base64': img_b64,
                'size_bytes': len(img_bytes),
                'method': 'file_fallback',
            }
        except Exception as e2:
            return {'error': f'Screenshot failed: {str(e)} / fallback: {str(e2)}'}


def handle_chop_data(body):
    """Read channel data from a CHOP."""
    path = body.get('path')
    channel_names = body.get('channels', None)  # list of names, or None for all
    sample_range = body.get('range', None)  # [start, end] or None for all

    if not path:
        return {'error': 'Missing required field: path'}

    node = op(path)
    if node is None:
        return {'error': f'Node not found: {path}'}

    if not node.isCHOP:
        return {'error': f'Node is not a CHOP: {path}'}

    result = {
        'path': path,
        'numChans': node.numChans,
        'numSamples': node.numSamples,
        'rate': node.rate,
        'channels': {},
    }

    for chan in node.chans():
        if channel_names and chan.name not in channel_names:
            continue

        samples = list(chan.vals)
        if sample_range:
            start = max(0, sample_range[0])
            end = min(len(samples), sample_range[1])
            samples = samples[start:end]

        # Limit to 1000 samples max to avoid huge responses
        if len(samples) > 1000:
            step = len(samples) // 1000
            samples = samples[::step]
            result['channels'][chan.name] = {
                'values': samples,
                'downsampled': True,
                'original_length': node.numSamples,
            }
        else:
            result['channels'][chan.name] = {
                'values': samples,
                'downsampled': False,
            }

    return result


def handle_sop_data(body):
    """Read geometry data from a SOP."""
    path = body.get('path')
    include_points = body.get('include_points', True)
    include_prims = body.get('include_prims', False)
    limit = body.get('limit', 500)

    if not path:
        return {'error': 'Missing required field: path'}

    node = op(path)
    if node is None:
        return {'error': f'Node not found: {path}'}

    if not node.isSOP:
        return {'error': f'Node is not a SOP: {path}'}

    result = {
        'path': path,
        'numPoints': node.numPoints,
        'numPrims': node.numPrims,
        'numVertices': node.numVertices,
    }

    if include_points:
        points = []
        for i, pt in enumerate(node.points()):
            if i >= limit:
                break
            points.append({
                'index': pt.index,
                'x': pt.x, 'y': pt.y, 'z': pt.z,
            })
        result['points'] = points
        result['points_truncated'] = node.numPoints > limit

    if include_prims:
        prims = []
        for i, prim in enumerate(node.prims()):
            if i >= limit:
                break
            prims.append({
                'index': prim.index,
                'numVertices': prim.numVertices,
            })
        result['prims'] = prims
        result['prims_truncated'] = node.numPrims > limit

    return result


def handle_cooking_info(body):
    """Get cooking/performance info for a node."""
    path = body.get('path', '/')
    recurse = body.get('recurse', False)
    sort_by = body.get('sort_by', 'cookTime')  # cookTime, cpuCookTime
    limit = body.get('limit', 20)

    node = op(path)
    if node is None:
        return {'error': f'Node not found: {path}'}

    results = []

    def collect_cook(n):
        try:
            results.append({
                'path': n.path,
                'name': n.name,
                'type': n.type,
                'cookTime': n.cookTime if hasattr(n, 'cookTime') else 0,
                'cpuCookTime': n.cpuCookTime if hasattr(n, 'cpuCookTime') else 0,
                'cookFrame': n.cookFrame if hasattr(n, 'cookFrame') else 0,
            })
        except Exception:
            pass
        if recurse and n.isCOMP:
            for child in n.children:
                collect_cook(child)

    collect_cook(node)

    # Sort
    results.sort(key=lambda x: x.get(sort_by, 0), reverse=True)
    results = results[:limit]

    return {
        'path': path,
        'fps': project.cookRate,
        'realTime': project.realTime,
        'frame': absTime.frame,
        'total_nodes': len(results),
        'nodes': results,
    }


def handle_search_nodes(body):
    """Search for nodes by name, type, or family."""
    query = body.get('query', '')
    search_path = body.get('path', '/')
    search_type = body.get('search_type', 'name')  # name, type, family, all
    limit = body.get('limit', 50)

    if not query:
        return {'error': 'Missing required field: query'}

    root = op(search_path)
    if root is None:
        return {'error': f'Search root not found: {search_path}'}

    query_lower = query.lower()
    results = []

    def search_recursive(n):
        if len(results) >= limit:
            return

        match = False
        if search_type in ('name', 'all') and query_lower in n.name.lower():
            match = True
        if search_type in ('type', 'all') and query_lower in n.type.lower():
            match = True
        if search_type in ('family', 'all') and query_lower in n.family.lower():
            match = True

        if match:
            results.append(_serialize_op(n))

        if n.isCOMP:
            for child in n.children:
                search_recursive(child)

    search_recursive(root)

    return {'query': query, 'search_type': search_type, 'count': len(results), 'nodes': results}


def handle_list_families(body):
    """List available operator families and types."""
    path = body.get('path', '/')

    root = op(path)
    if root is None:
        return {'error': f'Node not found: {path}'}

    families = {}

    def collect_types(n):
        fam = n.family
        if fam not in families:
            families[fam] = set()
        families[fam].add(n.type)
        if n.isCOMP:
            for child in n.children:
                collect_types(child)

    collect_types(root)

    return {
        'families': {k: sorted(list(v)) for k, v in sorted(families.items())},
    }


def handle_python_help(body):
    """Get Python help() output for a TD module/class."""
    target = body.get('target', '')
    if not target:
        return {'error': 'Missing required field: target (e.g. "td", "td.OP", "tdu")'}

    import io
    old_stdout = sys.stdout
    captured = io.StringIO()
    sys.stdout = captured

    try:
        help(eval(target))
    except Exception as e:
        sys.stdout = old_stdout
        return {'error': f'Help failed for "{target}": {str(e)}'}
    finally:
        sys.stdout = old_stdout

    help_text = captured.getvalue()
    # Truncate if too long
    if len(help_text) > 10000:
        help_text = help_text[:10000] + '\n\n... (truncated, use more specific target)'

    return {'target': target, 'help': help_text}


def handle_python_classes(body):
    """List available TouchDesigner Python classes."""
    try:
        import td
        classes = [name for name in dir(td) if not name.startswith('_')]
        return {'module': 'td', 'classes': classes, 'count': len(classes)}
    except Exception as e:
        return {'error': f'Failed to list classes: {str(e)}'}


def handle_timeline(body):
    """Get timeline/playback state."""
    return {
        'frame': absTime.frame,
        'seconds': absTime.seconds,
        'playing': project.realTime,
        'fps': project.cookRate,
        'start': project.cookRange[0] if hasattr(project, 'cookRange') else 1,
        'end': project.cookRange[1] if hasattr(project, 'cookRange') else 600,
    }


def handle_timeline_set(body):
    """Control timeline playback."""
    action = body.get('action')  # play, pause, frame
    frame = body.get('frame', None)
    fps = body.get('fps', None)

    if action == 'play':
        project.realTime = True
        return {'success': True, 'playing': True}
    elif action == 'pause':
        project.realTime = False
        return {'success': True, 'playing': False}
    elif action == 'frame' and frame is not None:
        absTime.frame = frame
        return {'success': True, 'frame': absTime.frame}
    elif fps is not None:
        project.cookRate = fps
        return {'success': True, 'fps': project.cookRate}
    else:
        return {'error': 'Provide action (play/pause/frame) or fps'}


def handle_pulse_param(body):
    """Pulse a pulse-type parameter."""
    path = body.get('path')
    param_name = body.get('param')

    if not path or not param_name:
        return {'error': 'Missing required fields: path and param'}

    node = op(path)
    if node is None:
        return {'error': f'Node not found: {path}'}

    p = getattr(node.par, param_name, None)
    if p is None:
        return {'error': f'Parameter not found: {param_name} on {path}'}

    try:
        p.pulse()
        return {'success': True, 'path': path, 'param': param_name}
    except Exception as e:
        return {'error': f'Failed to pulse: {str(e)}'}
