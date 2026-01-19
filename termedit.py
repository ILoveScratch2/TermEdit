#!/usr/bin/env python3
"""
TermEdit - 终端文本编辑器
By ILoveScratch2<ilovescratch@foxmail.com>
License: MPL-2.0
"""

from textual.app import App, ComposeResult
from textual.widgets import Static, Button, TextArea, DirectoryTree, Input, Label
from textual.containers import Horizontal, Vertical, Container
from textual.binding import Binding
from textual.screen import ModalScreen
from textual import events
from pathlib import Path
import sys


class ConfirmDialog(ModalScreen[bool]):
    BINDINGS = [
        Binding("escape", "cancel", "取消"),
        Binding("y", "yes", "是"),
        Binding("n", "no", "否"),
    ]
    
    def __init__(self, title: str, message: str):
        super().__init__()
        self.title_text = title
        self.message_text = message
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static(self.title_text, id="dialog-title"),
            Static(self.message_text, id="dialog-message"),
            Horizontal(
                Button("是(Y)", id="btn-yes", variant="primary"),
                Button("否(N)", id="btn-no", variant="default"),
                id="dialog-buttons"
            ),
            id="confirm-dialog"
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn-yes")
    
    def action_cancel(self) -> None:
        self.dismiss(False)
    
    def action_yes(self) -> None:
        self.dismiss(True)
    
    def action_no(self) -> None:
        self.dismiss(False)


class InputDialog(ModalScreen[str | None]):
    BINDINGS = [Binding("escape", "cancel", "取消")]
    
    def __init__(self, title: str, placeholder: str = "", default: str = ""):
        super().__init__()
        self.title_text = title
        self.placeholder = placeholder
        self.default = default
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static(self.title_text, id="dialog-title"),
            Input(value=self.default, placeholder=self.placeholder, id="dialog-input"),
            Horizontal(
                Button("确定", id="btn-ok", variant="primary"),
                Button("取消", id="btn-cancel", variant="default"),
                id="dialog-buttons"
            ),
            id="input-dialog"
        )
    
    def on_mount(self) -> None:
        self.query_one("#dialog-input", Input).focus()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-ok":
            value = self.query_one("#dialog-input", Input).value
            self.dismiss(value if value else None)
        else:
            self.dismiss(None)
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value if event.value else None)
    
    def action_cancel(self) -> None:
        self.dismiss(None)


class AboutDialog(ModalScreen[None]):
    BINDINGS = [Binding("escape", "dismiss", "关闭")]
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static("TermEdit v0.1", id="about-title"),
            Static(""),
            Static("终端UI文本编辑器"),
            Static("By ILoveScratch2"),
            Static("使用 Mozilla Public License 2.0 许可"),
            Static(""),
            Static("快捷键:"),
            Static("  Ctrl+N  新建    Ctrl+S  保存"),
            Static("  Ctrl+O  打开    Ctrl+Q  退出"),
            Static("  Ctrl+A  全选    Ctrl+Z  撤销"),
            Static("  Ctrl+C  复制    Ctrl+V  粘贴"),
            Static("  Ctrl+X  剪切    Ctrl+Y  重做"),
            Static(""),
            Button("关闭 (ESC)", id="btn-close", variant="primary"),
            id="about-dialog"
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()


class FileOpenDialog(ModalScreen[tuple[Path, str] | None]):    
    BINDINGS = [Binding("escape", "cancel", "取消")]
    
    def __init__(self, start_path: Path | None = None):
        super().__init__()
        self.start_path = start_path or Path.cwd()
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static("打开文件", id="dialog-title"),
            Input(value=str(self.start_path), id="path-input"),
            DirectoryTree(str(self.start_path), id="file-tree"),
            Horizontal(
                Label("编码: "),
                Input(placeholder="留空自动检测(utf-8/gbk)", id="encoding-input"),
                id="encoding-row"
            ),
            Horizontal(
                Button("打开", id="btn-open", variant="primary"),
                Button("取消", id="btn-cancel", variant="default"),
                id="dialog-buttons"
            ),
            id="file-dialog"
        )
    
    def on_mount(self) -> None:
        tree = self.query_one("#file-tree", DirectoryTree)
        tree.focus()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "path-input":
            path = Path(event.value)
            if path.exists():
                if path.is_file():
                    encoding = self.query_one("#encoding-input", Input).value.strip()
                    self.dismiss((path, encoding))
                else:
                    self._navigate_to(path)
            else:
                self.notify("路径不存在", severity="warning")
    
    def _navigate_to(self, path: Path) -> None:
        try:
            tree = self.query_one("#file-tree", DirectoryTree)
            tree.path = path
            tree.reload()
            tree.focus()
            self.query_one("#path-input", Input).value = str(path)
        except Exception as e:
            self.notify(f"无法导航: {e}", severity="error")
    
    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        encoding = self.query_one("#encoding-input", Input).value.strip()
        self.dismiss((event.path, encoding))
    
    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        self.query_one("#path-input", Input).value = str(event.path)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-open":
            encoding = self.query_one("#encoding-input", Input).value.strip()
            path_input = self.query_one("#path-input", Input).value
            path = Path(path_input)
            if path.exists() and path.is_file():
                self.dismiss((path, encoding))
                return
            tree = self.query_one("#file-tree", DirectoryTree)
            if tree.cursor_node and tree.cursor_node.data:
                path = tree.cursor_node.data.path
                if path.is_file():
                    self.dismiss((path, encoding))
                else:
                    self.notify("请选择一个文件", severity="warning")
            else:
                self.notify("请选择一个文件", severity="warning")
        else:
            self.dismiss(None)
    
    def action_cancel(self) -> None:
        self.dismiss(None)


class FileSaveDialog(ModalScreen[Path | None]):
    BINDINGS = [Binding("escape", "cancel", "取消")]
    
    def __init__(self, start_path: Path | None = None, default_name: str = ""):
        super().__init__()
        self.start_path = start_path or Path.cwd()
        self.default_name = default_name
        self.current_dir = self.start_path
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static("保存文件", id="dialog-title"),
            Input(value=str(self.start_path), id="path-input"),
            DirectoryTree(str(self.start_path), id="file-tree"),
            Horizontal(
                Label("文件名: "),
                Input(value=self.default_name, placeholder="输入文件名", id="filename-input"),
                id="filename-row"
            ),
            Horizontal(
                Button("保存", id="btn-save", variant="primary"),
                Button("取消", id="btn-cancel", variant="default"),
                id="dialog-buttons"
            ),
            id="file-dialog"
        )
    
    def on_mount(self) -> None:
        self.query_one("#filename-input", Input).focus()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "path-input":
            path = Path(event.value)
            if path.exists() and path.is_dir():
                self.current_dir = path
                self._navigate_to(path)
            elif path.exists() and path.is_file():
                self.current_dir = path.parent
                self.query_one("#filename-input", Input).value = path.name
                self._navigate_to(path.parent)
            else:
                self.notify("路径不存在", severity="warning")
        elif event.input.id == "filename-input":
            filename = event.value.strip()
            if filename:
                self.dismiss(self.current_dir / filename)
    
    def _navigate_to(self, path: Path) -> None:
        try:
            tree = self.query_one("#file-tree", DirectoryTree)
            tree.path = path
            tree.reload()
            self.query_one("#path-input", Input).value = str(path)
        except Exception as e:
            self.notify(f"无法导航: {e}", severity="error")
    
    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        self.current_dir = event.path
        self.query_one("#path-input", Input).value = str(event.path)
    
    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.current_dir = event.path.parent
        self.query_one("#filename-input", Input).value = event.path.name
        self.query_one("#path-input", Input).value = str(event.path.parent)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            filename = self.query_one("#filename-input", Input).value.strip()
            if filename:
                self.dismiss(self.current_dir / filename)
            else:
                self.notify("请输入文件名", severity="warning")
        else:
            self.dismiss(None)
    
    def action_cancel(self) -> None:
        self.dismiss(None)


class MenuBar(Horizontal):
    def compose(self) -> ComposeResult:
        yield Button(" 文件(F) ", id="menu-file", classes="menu-btn")
        yield Button(" 编辑(E) ", id="menu-edit", classes="menu-btn")
        yield Button(" 关于(A) ", id="menu-about", classes="menu-btn")


class FileMenu(Vertical):
    def compose(self) -> ComposeResult:
        yield Button("新建        Ctrl+N", id="act-new", classes="menu-item")
        yield Button("打开        Ctrl+O", id="act-open", classes="menu-item")
        yield Button("保存        Ctrl+S", id="act-save", classes="menu-item")
        yield Button("另存为...        ", id="act-saveas", classes="menu-item")
        yield Static("─" * 22, classes="menu-sep")
        yield Button("退出        Ctrl+Q", id="act-exit", classes="menu-item")


class EditMenu(Vertical):  
    def compose(self) -> ComposeResult:
        yield Button("撤销        Ctrl+Z", id="act-undo", classes="menu-item")
        yield Button("重做        Ctrl+Y", id="act-redo", classes="menu-item")
        yield Static("─" * 22, classes="menu-sep")
        yield Button("剪切        Ctrl+X", id="act-cut", classes="menu-item")
        yield Button("复制        Ctrl+C", id="act-copy", classes="menu-item")
        yield Button("粘贴        Ctrl+V", id="act-paste", classes="menu-item")
        yield Static("─" * 22, classes="menu-sep")
        yield Button("全选        Ctrl+A", id="act-selall", classes="menu-item")


class StatusBar(Horizontal):
    def compose(self) -> ComposeResult:
        yield Static("行: 1", id="st-line")
        yield Static("列: 1", id="st-col")
        yield Static("字数: 0", id="st-words")
        yield Static("", id="st-file")


class TermEdit(App):
    """
    TermEdit - By ILoveScratch2
    """
    
    CSS = """
    Screen {
        background: #1e1e1e;
    }
    
    /* 菜单栏 */
    MenuBar {
        dock: top;
        height: 1;
        background: #0078d4;
        padding: 0;
    }
    
    .menu-btn {
        min-width: 12;
        height: 1;
        border: none;
        background: #0078d4;
        color: white;
        padding: 0;
        margin: 0;
    }
    
    .menu-btn:hover {
        background: #106ebe;
    }
    
    .menu-btn:focus {
        background: #005a9e;
    }
    
    /* 下拉菜单 */
    FileMenu, EditMenu {
        width: 26;
        height: auto;
        max-height: 12;
        background: #252526;
        border: solid #0078d4;
        layer: menu;
        position: absolute;
        offset: 0 1;
    }
    
    EditMenu {
        offset: 12 1;
    }
    
    .menu-item {
        width: 100%;
        height: 1;
        border: none;
        background: #252526;
        color: #cccccc;
        text-align: left;
        padding: 0 1;
    }
    
    .menu-item:hover {
        background: #0078d4;
        color: white;
    }
    
    .menu-sep {
        width: 100%;
        height: 1;
        color: #4a4a4a;
        padding: 0 1;
    }
    
    /* 编辑器 */
    #editor {
        height: 1fr;
        border: none;
        background: #1e1e1e;
    }
    
    /* 状态栏 */
    StatusBar {
        dock: bottom;
        height: 1;
        background: #0078d4;
        padding: 0 1;
    }
    
    StatusBar > Static {
        width: auto;
        min-width: 12;
        color: white;
        padding: 0 1;
    }
    
    #st-file {
        width: 1fr;
        text-align: right;
    }
    
    /* 对话框通用样式 */
    #confirm-dialog, #input-dialog, #about-dialog {
        width: 50;
        height: auto;
        max-height: 20;
        background: #252526;
        border: solid #0078d4;
        padding: 1 2;
    }
    
    #file-dialog {
        width: 70;
        height: 25;
        background: #252526;
        border: solid #0078d4;
        padding: 1 2;
    }
    
    #dialog-title, #about-title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: #0078d4;
        padding-bottom: 1;
    }
    
    #dialog-message {
        width: 100%;
        text-align: center;
        padding-bottom: 1;
        color: #cccccc;
    }
    
    #dialog-buttons {
        width: 100%;
        height: 3;
        align: center middle;
        padding-top: 1;
    }
    
    #dialog-buttons > Button {
        margin: 0 1;
    }
    
    #file-tree {
        height: 1fr;
        border: solid #3c3c3c;
        background: #1e1e1e;
        margin-bottom: 1;
    }
    
    #path-input {
        width: 100%;
        margin-bottom: 1;
    }
    
    #filename-row {
        width: 100%;
        height: 3;
        padding: 0;
    }
    
    #filename-row > Label {
        width: auto;
        padding: 1 0;
        color: #cccccc;
    }
    
    #filename-row > Input {
        width: 1fr;
    }
    
    #encoding-row {
        width: 100%;
        height: 3;
        padding: 0;
        margin-bottom: 1;
    }
    
    #encoding-row > Label {
        width: auto;
        padding: 1 0;
        color: #cccccc;
    }
    
    #encoding-row > Input {
        width: 1fr;
    }
    
    #about-dialog {
        width: 45;
        height: auto;
    }
    
    #about-dialog > Static {
        width: 100%;
        color: #cccccc;
    }
    
    #btn-close {
        margin-top: 1;
        width: 100%;
    }

    /* 对话框居中 */
    ConfirmDialog, InputDialog, AboutDialog, FileOpenDialog, FileSaveDialog {
        align: center middle;
    }
    """
    
    BINDINGS = [
        # 文件操作
        Binding("ctrl+n", "new_file", "新建", show=False),
        Binding("ctrl+o", "open_file", "打开", show=False),
        Binding("ctrl+s", "save_file", "保存", show=False),
        Binding("ctrl+shift+s", "save_as", "另存为", show=False),
        Binding("ctrl+q", "quit_app", "退出", show=False),
        # 编辑操作
        Binding("ctrl+z", "undo", "撤销", show=False),
        Binding("ctrl+y", "redo", "重做", show=False),
        Binding("ctrl+a", "select_all", "全选", show=False),
        Binding("ctrl+c", "copy", "复制", show=False),
        Binding("ctrl+x", "cut", "剪切", show=False),
        Binding("ctrl+v", "paste", "粘贴", show=False),
        # UI
        Binding("f10", "toggle_menu", "菜单", show=False),
        Binding("escape", "close_menu", "关闭", show=False),
    ]
    
    def __init__(self, filepath: str | None = None):
        super().__init__()
        self.current_file: Path | None = Path(filepath) if filepath else None
        self.modified: bool = False
        self.menu_open: str | None = None
        self._force_quit: bool = False
    
    def compose(self) -> ComposeResult:
        yield MenuBar()
        yield TextArea(id="editor", show_line_numbers=True)
        yield StatusBar()
    
    def on_mount(self) -> None:
        editor = self.query_one("#editor", TextArea)
        editor.focus()
        
        if self.current_file and self.current_file.exists():
            self._load_file(self.current_file)
        
        self._update_status()


    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        self.modified = True
        self._update_status()
    
    def on_text_area_selection_changed(self, event: TextArea.SelectionChanged) -> None:
        self._update_status()
    
    def _update_status(self) -> None:
        editor = self.query_one("#editor", TextArea)
        
        cursor = editor.cursor_location
        line, col = cursor[0] + 1, cursor[1] + 1
        
        text = editor.text
        words = len(text.split()) if text.strip() else 0
        
        self.query_one("#st-line", Static).update(f"行: {line}")
        self.query_one("#st-col", Static).update(f"列: {col}")
        self.query_one("#st-words", Static).update(f"字数: {words}")
        
        if self.current_file:
            name = self.current_file.name + (" *" if self.modified else "")
        else:
            name = "[未命名]" + (" *" if self.modified else "")
        self.query_one("#st-file", Static).update(name)
    
    def _load_file(self, path: Path, encoding: str = "") -> None:
        try:
            # 如果指定了编码，使用指定的编码
            if encoding:
                content = path.read_text(encoding=encoding)
                used_encoding = encoding
            else:
                # 尝试使用 utf-8，失败则尝试 gbk
                try:
                    content = path.read_text(encoding="utf-8")
                    used_encoding = "utf-8"
                except UnicodeDecodeError:
                    content = path.read_text(encoding="gbk")
                    used_encoding = "gbk"
            
            editor = self.query_one("#editor", TextArea)
            editor.text = content
            self.current_file = path
            self.modified = False
            self._update_status()
            self.notify(f"已打开: {path.name} (编码: {used_encoding})")
        except Exception as e:
            self.notify(f"无法打开: {e}", severity="error")
    
    def _save_to_file(self, path: Path) -> None:
        try:
            editor = self.query_one("#editor", TextArea)
            path.write_text(editor.text, encoding="utf-8")
            self.current_file = path
            self.modified = False
            self._update_status()
            self.notify(f"已保存: {path.name}")
        except Exception as e:
            self.notify(f"无法保存: {e}", severity="error")
    
    def _check_modified_then(self, callback) -> None:
        if self.modified:
            def handle_result(discard: bool) -> None:
                if discard:
                    callback()
            
            self.push_screen(
                ConfirmDialog("放弃更改?", "当前文件有未保存的修改，是否放弃?"),
                handle_result
            )
        else:
            callback()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id

        if btn_id == "menu-file":
            self._toggle_menu("file")
        elif btn_id == "menu-edit":
            self._toggle_menu("edit")
        elif btn_id == "menu-about":
            self._close_menus()
            self.push_screen(AboutDialog())

        elif btn_id == "act-new":
            self._close_menus()
            self.action_new_file()
        elif btn_id == "act-open":
            self._close_menus()
            self.action_open_file()
        elif btn_id == "act-save":
            self._close_menus()
            self.action_save_file()
        elif btn_id == "act-saveas":
            self._close_menus()
            self.action_save_as()
        elif btn_id == "act-exit":
            self._close_menus()
            self.action_quit_app()

        elif btn_id == "act-undo":
            self._close_menus()
            self.action_undo()
        elif btn_id == "act-redo":
            self._close_menus()
            self.action_redo()
        elif btn_id == "act-cut":
            self._close_menus()
            self.action_cut()
        elif btn_id == "act-copy":
            self._close_menus()
            self.action_copy()
        elif btn_id == "act-paste":
            self._close_menus()
            self.action_paste()
        elif btn_id == "act-selall":
            self._close_menus()
            self.action_select_all()
    
    def _toggle_menu(self, menu: str) -> None:
        if self.menu_open == menu:
            self._close_menus()
        else:
            self._close_menus()
            if menu == "file":
                self.mount(FileMenu(id="dropdown-file"))
            elif menu == "edit":
                self.mount(EditMenu(id="dropdown-edit"))
            self.menu_open = menu
    
    def _close_menus(self) -> None:
        for menu_id in ["dropdown-file", "dropdown-edit"]:
            try:
                self.query_one(f"#{menu_id}").remove()
            except:
                pass
        self.menu_open = None
        try:
            self.query_one("#editor", TextArea).focus()
        except:
            pass

    def action_new_file(self) -> None:
        def do_new():
            editor = self.query_one("#editor", TextArea)
            editor.text = ""
            self.current_file = None
            self.modified = False
            self._update_status()
        
        self._check_modified_then(do_new)
    
    def action_open_file(self) -> None:
        def do_open():
            start = self.current_file.parent if self.current_file else Path.cwd()
            
            def handle_path(result: tuple[Path, str] | None) -> None:
                if result:
                    path, encoding = result
                    self._load_file(path, encoding)
            
            self.push_screen(FileOpenDialog(start), handle_path)
        
        self._check_modified_then(do_open)
    
    def action_save_file(self) -> None:
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self.action_save_as()
    
    def action_save_as(self) -> None:
        start = self.current_file.parent if self.current_file else Path.cwd()
        default = self.current_file.name if self.current_file else ""
        
        def handle_path(path: Path | None) -> None:
            if path:
                self._save_to_file(path)
        
        self.push_screen(FileSaveDialog(start, default), handle_path)
    
    def action_quit_app(self) -> None:
        if self.modified and not self._force_quit:
            def handle_quit(discard: bool) -> None:
                if discard:
                    self.exit()
            
            self.push_screen(
                ConfirmDialog("退出?", "有未保存的修改，确定退出吗?"),
                handle_quit
            )
        else:
            self.exit()
    
    def action_undo(self) -> None:
        self.query_one("#editor", TextArea).undo()
    
    def action_redo(self) -> None:
        self.query_one("#editor", TextArea).redo()
    
    def action_select_all(self) -> None:
        self.query_one("#editor", TextArea).select_all()
    
    def action_copy(self) -> None:
        self.query_one("#editor", TextArea).action_copy()
    
    def action_cut(self) -> None:
        self.query_one("#editor", TextArea).action_cut()
    
    def action_paste(self) -> None:
        self.query_one("#editor", TextArea).action_paste()
    
    def action_toggle_menu(self) -> None:
        self._toggle_menu("file")
    
    def action_close_menu(self) -> None:
        if self.menu_open:
            self._close_menus()
    
    def on_click(self, event: events.Click) -> None:
        if self.menu_open and event.y > 10:
            self._close_menus()


def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else None
    app = TermEdit(filepath)
    app.run()


if __name__ == "__main__":
    main()
