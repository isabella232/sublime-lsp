from .reference import RefInfo
from .lsp_client import ServerClient, WorkerClient
from .client_manager import LspClientManager
# from .node_client import ServerClient, WorkerClient
from .service_proxy import ServiceProxy
from .global_vars import *
from . import global_vars
import copy

class ClientFileInfo:
    """per-file, globally-accessible information"""

    def __init__(self, filename):
        self.filename = filename
        self.pending_changes = False
        self.change_count = 0
        self.errors = {
            'syntacticDiag': [],
            'semanticDiag': [],
        }
        self.rename_on_load = None


class EditorClient:
    """A singleton class holding information for the entire application that must be accessible globally"""

    def __init__(self):
        self.file_map = {}
        self.ref_info = None
        self.seq_to_tempfile_name = {}
        self.available_tempfile_list = []
        self.tmpseq = 0
        # self.node_client = None
        # self.worker_client = None
        self.initialized = False

        self.tab_size = 4
        self.indent_size = self.tab_size
        self.translate_tab_to_spaces = False
        self.ts_auto_format_enabled = True
        self.ts_auto_indent_enabled = True
        self.auto_match_enabled = True
        self.client_manager = LspClientManager()

    def go_specific_hack(self, env):
        gopaths = env["GOPATH"].split(os.pathsep)
        for gopath in gopaths:
            env["PATH"] = os.path.join(gopath, "bin")+os.pathsep+env["PATH"]

    def initialize_client_manager(self, settings):
        # initialize client manager
        clients = settings.get("clients")
        if clients:
            for client in clients:
                env = copy.deepcopy(os.environ)
                path_additions = client.get("path_additions")
                if path_additions:
                    env["PATH"] = os.pathsep.join(path_additions)+os.pathsep+env["PATH"]
                additional_env = client.get("env")
                if additional_env:
                    env.update(additional_env)
                    if "go" in client["file_exts"]:
                        self.go_specific_hack(env)
                self.client_manager.register_extensions(
                    client["file_exts"], 
                    client["binary"],
                    client.get("args"), 
                    env)

    def get_root_path(self):
        # hack, because the Sublime API is broken and .get('folder') returns the
        # top folder always
        file_path = sublime.active_window().extract_variables().get('file_path')
        if not file_path:
            return None

        found_folder = sublime.active_window().extract_variables().get('folder')
        chars_matching = -1
        for folder in sublime.active_window().folders():
            if file_path.startswith(folder) and len(folder) > chars_matching:
                found_folder = folder
                chars_matching = len(found_folder)
        return found_folder

    def get_service(self):
        file_ext = sublime.active_window().extract_variables().get('file_extension')
        root_path = self.get_root_path()
        return self.client_manager.get_client(file_ext, root_path)

    def initialize(self):
        """
        Sublime_api methods can only be executed in plugin_loaded, and they will
        return None if executed during import time. Therefore the cli needs to be
        initialized during loading time
        """

        # retrieve the path to tsserver.js
        # first see if user set the path to the file
        settings = sublime.load_settings("Preferences.sublime-settings")
        self.initialize_client_manager(settings)
        tsdk_location = settings.get("typescript_tsdk")
        if tsdk_location:
            proc_file = os.path.join(tsdk_location, "tsserver.js")
            global_vars._tsc_path = os.path.join(tsdk_location, "tsc.js")
        else:
            # otherwise, get tsserver.js from package directory
            proc_file = os.path.join(PLUGIN_DIR, "tsserver", "tsserver.js")
            global_vars._tsc_path = os.path.join(PLUGIN_DIR, "tsserver", "tsc.js")
        print("Path of tsserver.js: " + proc_file)
        print("Path of tsc.js: " + get_tsc_path())

        # self.node_client = ServerClient(proc_file)
        # self.worker_client = WorkerClient(proc_file)
        # self.service = ServiceProxy(self.worker_client, self.node_client)

        # load formatting settings and set callbacks for setting changes
        for setting_name in [
            'tab_size',
            'indent_size',
            'translate_tabs_to_spaces',
            'typescript_auto_format',
            'typescript_auto_indent',
            'auto_match_enabled'
        ]:
            settings.add_on_change(setting_name, self.load_format_settings)
        self.load_format_settings()

        self.initialized = True

    def load_format_settings(self):
        settings = sublime.load_settings('Preferences.sublime-settings')
        self.tab_size = settings.get('tab_size', 4)
        self.indent_size = settings.get('indent_size', self.tab_size)
        self.translate_tab_to_spaces = settings.get('translate_tabs_to_spaces', False)
        self.ts_auto_format_enabled = settings.get("typescript_auto_format")
        self.ts_auto_indent_enabled = settings.get("typescript_auto_indent")
        self.auto_match_enabled = settings.get("auto_match_enabled")
        self.set_features()

    def set_features(self):
        host_info = "Sublime Text version " + str(sublime.version())
        # Preferences Settings
        format_options = {
            "tabSize": self.tab_size,
            "indentSize": self.indent_size,
            "convertTabsToSpaces": self.translate_tab_to_spaces
        }
        self.get_service().configure(host_info, None, format_options)

    # ref info is for Find References view
    # TODO: generalize this so that there can be multiple
    # for example, one for Find References and one for build errors
    def dispose_ref_info(self):
        self.ref_info = None

    def init_ref_info(self, first_line, ref_id):
        self.ref_info = RefInfo(first_line, ref_id)
        return self.ref_info

    def update_ref_info(self, ref_info):
        self.ref_info = ref_info

    def get_ref_info(self):
        return self.ref_info

    def get_or_add_file(self, filename):
        """Get or add per-file information that must be globally accessible """
        if os.name == "nt" and filename:
            filename = filename.replace('/', '\\')
        if filename not in self.file_map:
            client_info = ClientFileInfo(filename)
            self.file_map[filename] = client_info
        else:
            client_info = self.file_map[filename]
        return client_info

    def has_errors(self, filename):
        client_info = self.get_or_add_file(filename)
        return len(client_info.errors['syntacticDiag']) > 0 or len(client_info.errors['semanticDiag']) > 0

# The globally accessible instance
cli = EditorClient()
