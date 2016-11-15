from .lsp_client import ServerClient, WorkerClient
from .service_proxy import ServiceProxy
from .logger import log

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
            log.debug('Registered binary {0} for extension {1}'.format(binary_name, file_ext))
            self.extension_mapping[file_ext] = (binary_name, args if args else [], env)

    def get_client(self, file_ext, root_path):
        log.debug('Looking for client for extension {0} in {1}'.format(file_ext, root_path))
        if file_ext not in self.extension_mapping:
            log.debug('Extension {0} is not supported yet'.format(file_ext))
            return None
            # return FileExtensionNotRegistered(file_ext)
        binary_name, args, env = self.extension_mapping[file_ext]
        key = (root_path, binary_name)
        if key in self.client_mapping:
            log.debug('Using existing client')
            return self.client_mapping[key]
        try:
            log.debug('Instantiating new client using binary {0} for extension {1} in {2}'.format(binary_name, file_ext, root_path))
            node_client = ServerClient(binary_name, args, env, root_path)
            worker_client = WorkerClient(binary_name, args, env, root_path)
            service = ServiceProxy(worker_client, node_client)
            self.client_mapping[key] = service
            return service
        except Exception as err:
            # Deal with process init failure
            return None
            # return ProcessFailsToStart(
            #     file_ext, binary_name, args, env)

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
