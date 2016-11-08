import sublime_plugin
from ..libs.global_vars import get_language_service_enabled
from ..libs.view_helpers import is_supported_ext, active_view


class TypeScriptBaseTextCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        return is_supported_ext(self.view) and get_language_service_enabled()


class TypeScriptBaseWindowCommand(sublime_plugin.WindowCommand):
    def is_enabled(self):
        return is_supported_ext(self.window.active_view()) and get_language_service_enabled()


class TypeScriptBaseApplicationCommand(sublime_plugin.ApplicationCommand):
    def is_enabled(self):
        return is_supported_ext(active_view()) and get_language_service_enabled()
