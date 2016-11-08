from ..libs.view_helpers import *
from ..libs.reference import *
from .base_command import TypeScriptBaseTextCommand
from ..libs.editor_client import get_root_path
from ..libs.git_helpers import get_url_struct
import webbrowser


class BrowseCode(TypeScriptBaseTextCommand):
    """Browse code on Sourcegraph.com"""
    def run(self, text):
        check_update_view(self.view)
        # TODO check that this file isn't dirty. Won't sync with line numbers if so.
        root_directory = get_root_path()
        file_path = sublime.active_window().extract_variables().get('file')
        git_url_struct = get_url_struct(root_directory, file_path)
        row, col = self.view.rowcol(self.view.sel()[0].begin())
        print(git_url_struct)
        sourcegraph_url = "https://sourcegraph.com/"+git_url_struct[0]+"@"+git_url_struct[1]+"/-/blob/"+git_url_struct[2]+"#L"+str(row+1)
        print(sourcegraph_url)
        webbrowser.open(sourcegraph_url)

    def is_visible(self):
        return True
