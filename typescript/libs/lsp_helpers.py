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
    new_cmd = {
        "id": old_cmd["seq"],
        "jsonrpc": "2.0"
    }
    if command == "quickinfo" or command == "definition":
        new_cmd["method"] = "textDocument/hover" if command == "quickinfo" else "textDocument/definition"
        new_cmd["params"] = {
            "position": convert_position_to_lsp(args),
            "textDocument": {
                "uri": filename_to_uri(args["file"])
            }
        }
        return new_cmd
    elif command == "change":
        new_cmd["method"] = "textDocument/didChange"
        new_cmd["params"] = {
            "textDocument": {
                "uri": filename_to_uri(args["file"]),
                "version": 1
            },
            "contentChanges": convert_change_to_lsp(args)
        }
        return new_cmd
    elif command == "open":
        new_cmd["method"] = "textDocument/didOpen"
        new_cmd["params"] = {
            "textDocument": {
                "uri": filename_to_uri(args["file"]),
                "languageId": "go",
                "version": 0,
                "text": args["text"]
            },
        }
        return new_cmd
    elif command == "references":
        new_cmd["method"] = "textDocument/references"
        new_cmd["params"] = {
            "position": convert_position_to_lsp(args),
            "textDocument": {
                "uri": filename_to_uri(args["file"])
            },
            "includeDeclaration": False,
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


def convert_range_to_lsp(args):
        return {
            "start": {
                "line": args["line"] - 1,
                "character": args["offset"] - 1
            },
            "end": {
                "line": args["endLine"] - 1,
                "character": args["endOffset"] - 1
            }
        }


def convert_position_from_lsp(args):
    return {
        "line": args["line"],
        "offset": args["character"]
    }


def convert_change_to_lsp(args):
    return [
        {
            # "range": convert_range_to_lsp(args),
            # "rangeLength": 5,
            "text": args["insertString"]
        }
    ]


def convert_filename_to_lsp(args, version=None):
    return_val = {
        "uri": filename_to_uri(args["file"])
    }
    if version:
        return_val["version"] = version
    return return_val


def filename_to_uri(filename):
    return "file://"+filename


def convert_lsp_to_filename(uri):
    return uri[len("file://"):]


def format_request(request):
    """Converts the request into json and adds the Content-Length header"""
    content = json.dumps(request, indent=2)
    content_length = len(content)

    result = "Content-Length: {}\r\n\r\n{}".format(content_length, content)
    return result


def convert_other(msg):
    if not msg.get("params"):
        return None
    params = msg["params"]
    if params.get("diagnostics"):
        diag = params.get("diagnostics")[0]
        return {
            "event": "syntaxDiag",
            "type": "event",
            "seq": 0,
            "body": {
                "file": convert_lsp_to_filename(params["uri"]),
                "diagnostics": [{
                    "text": diag["message"],
                    "start": {
                        "line": diag["range"]["start"]["line"]+1,
                        "offset": diag["range"]["start"]["character"]+1,
                    },
                    "end": {
                        "line": diag["range"]["end"]["line"]+1,
                        "offset": diag["range"]["end"]["character"]+2,
                    },
                }]
            }
        }
    return None


def convert_response(request_type, response):
    if response.get("id") == 0:
        return None
    success = response.get("result") is not None
    if not success:
        return None
    if not response.get("result"):
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
    elif request_type == "textDocument/references":
        referencesRespBody = {
                "refs": [],
                "symbolName": "SymbolName",
                "symbolDisplayString": "SymbolText",
                "symbolStartOffset": 17
            }
        for entry in response["result"]:
            referencesRespBody["refs"].append({
                "end": convert_position_from_lsp(entry["range"]["end"]),
                "start": convert_position_from_lsp(entry["range"]["start"]),
                "isDefinition": False,
                "isWriteAccess": True,
                "file": convert_lsp_to_filename(entry["uri"]),
                "lineText": "RandomText",
            })
        return {
            "seq": 0,
            "request_seq": response["id"],
            "success": success,
            "command": "references",
            "body": referencesRespBody,
            "type": "response"
        }

    return None


# file_name = args["filename"]
#         line = args["line"]
#         ref_display_string = args["referencesRespBody"]["symbolDisplayString"]
#         ref_id = args["referencesRespBody"]["symbolName"]
#         refs = args["referencesRespBody"]["refs"]