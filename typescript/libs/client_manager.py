from .lsp_client import ServerClient, WorkerClient
from .service_proxy import ServiceProxy
import json
import threading
try:
    from Queue import Queue
except ImportError:
    from queue import Queue  # python 3.x


class LspClientManager():

    def __init__(self):
        self.client_mapping = {}
        self.extension_mapping = {}
        self.response_queue = Queue()
        self.lock = threading.Lock()

    def register_extensions(self, file_exts, binary_name, args, env):
        for file_ext in file_exts:
            self.extension_mapping[file_ext] = (binary_name, args if args else [], env)

    def get_client(self, file_ext, root_path):
        if file_ext not in self.extension_mapping:
            return FileExtensionNotRegistered(file_ext)
        binary_name, args, env = self.extension_mapping[file_ext]
        key = (root_path, binary_name)
        if key in self.client_mapping:
            return self.client_mapping[key]
        try:
            print("HERE1")
            node_client = ServerClient(binary_name, args, env, root_path)
            print("HERE2")
            worker_client = WorkerClient(binary_name, args, env, root_path)
            print("HERE3")
            service = ServiceProxy(worker_client, node_client)
            print("HERE4")
            self.client_mapping[key] = service
            return service
        except Exception as err:
            # Deal with process init failure
            print(err)
            return ProcessFailsToStart(
                file_ext, binary_name, args, env)

    def has_extension(self, ext):
        return self.extension_mapping.get(ext) is not None

    def get_clients(self):
        return self.client_mapping.values()


class ClientManagerError():
    pass


class FileExtensionNotRegistered(ClientManagerError):

    def __init__(self, file_ext):
        self.file_ext = file_ext
        self.message = "File extension %s doesn't have a registered LSP binary." % (
            self.file_ext)


class ProcessFailsToStart(ClientManagerError):

    def __init__(self, file_ext, binary_name, args, env):
        self.file_ext = file_ext
        self.message = "Failed to start LSP client %s registered for extension %s with args %s and env %s" % (
            file_ext, binary_name, args, env)
