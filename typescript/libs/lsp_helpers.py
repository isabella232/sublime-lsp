from . import json_helpers
import json


def init_message(root_path, process_id):
    cmd = {
        "id": 0,
        "method": "initialize",
        "jsonrpc": "2.0",
        "params": {
            "processId": process_id,
            "rootPath": root_path,
            "capabilities": {},
        }
    }
    return json_helpers.encode(cmd)


def convert_cmd(str_cmd):
    old_cmd = json_helpers.decode(str_cmd)

    # shortcut if it is hand-jammed init message
    if old_cmd.get("method"):
        return old_cmd

    args = old_cmd.get("arguments")
    command = old_cmd["command"]
    print("COMMAND IS %s" % command)
    new_cmd = {
        "id": old_cmd["seq"],
        "jsonrpc": "2.0"
    }
    if command == "quickinfo" or command == "definition":
        new_cmd["method"] = "textDocument/hover" if command == "quickinfo" else "textDocument/definition"
        new_cmd["params"] = {
            "position": convert_position_to_lsp(args),
            "textDocument": convert_filename_to_lsp(args)
        }
        return new_cmd
    return None


def to_lsp_method(method):
    if method == "quickinfo":
        return "textDocument/hover"
    if method == "definition":
        return "textDocument/definition"


def convert_position_to_lsp(args):
        return {
            "line": args["line"] - 1,
            "character": args["offset"] - 1
        }


def convert_position_from_lsp(args):
    return {
        "line": args["line"],
        "offset": args["character"]
    }


def convert_filename_to_lsp(args):
    return {
        "uri": "file://"+args["file"]
    }


def convert_lsp_to_filename(uri):
    return uri[len("file://"):]


def format_request(request):
    """Converts the request into json and adds the Content-Length header"""
    content = json.dumps(request, indent=2)
    content_length = len(content)

    result = "Content-Length: {}\r\n\r\n{}".format(content_length, content)
    return result


def convert_response(request_type, response):
    if response["id"] == 0:
        return None
    success = response.get("result") is not None
    if not success:
        return None
    if request_type == "textDocument/hover":
        first_result = response["result"]
        return {
            "seq": 0,
            "request_seq": response["id"],
            "success": success,
            "command": "quickinfo",
            "body": {
                "displayString": first_result["contents"][0]["value"],
                "start": convert_position_from_lsp(first_result["range"]["start"]),
                "kind": "alias",
                "end": convert_position_from_lsp(first_result["range"]["end"]),
                "kindModifiers": "",
                "documentation": ""
            },
            "type": "response"
        }
    elif request_type == "textDocument/definition":
        first_result = response["result"][0]
        return {
            "seq": 0,
            "request_seq": response["id"],
            "success": success,
            "command": "definition",
            "body": [{
                "start": convert_position_from_lsp(first_result["range"]["start"]),
                "end": convert_position_from_lsp(first_result["range"]["end"]),
                "file": convert_lsp_to_filename(first_result["uri"]),
                "kindModifiers": "",
                "documentation": ""
            }],
            "type": "response"
        }
    return None
