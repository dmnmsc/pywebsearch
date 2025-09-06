import gettext
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QMessageBox,
    QRadioButton,
    QVBoxLayout,
    QFileDialog,
)
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl
import os


_ = gettext.gettext


class Dialogs:
    def __init__(self, parent=None):
        self.parent = parent

    def show_message_box(
        self, text, title="KWebSearch", icon=QMessageBox.Icon.Information
    ):
        msg = QMessageBox(self.parent)
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def show_yes_no_box(
        self, text, title="KWebSearch", default_button=QMessageBox.StandardButton.No
    ):
        reply = QMessageBox.question(
            self.parent,
            title,
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            default_button,
        )
        return reply == QMessageBox.StandardButton.Yes

    def get_input(self, title, label, text="", select_text=False):
        input_dialog = QInputDialog(self.parent)
        input_dialog.setWindowFlags(
            input_dialog.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        input_dialog.setWindowTitle(title)
        input_dialog.setLabelText(label)
        input_dialog.setTextValue(text)
        if select_text:
            input_dialog.findChild(QLineEdit).selectAll()
        if input_dialog.exec():
            return input_dialog.textValue()
        return None

    def show_list_dialog(self, title, label, items, radio=False):
        dialog = QDialog(self.parent)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(label))
        if radio:
            radio_buttons = []
            for i, (text, checked) in enumerate(items):
                radio_button = QRadioButton(text)
                radio_button.setChecked(checked)
                layout.addWidget(radio_button)
                radio_buttons.append((str(i + 1), radio_button))
        else:
            combo = QComboBox()
            combo.addItems(items)
            layout.addWidget(combo)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.setLayout(layout)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if radio:
                for val, button in radio_buttons:
                    if button.isChecked():
                        return val
            else:
                return combo.currentText()
        return None

    def show_searchable_list_dialog(self, title, label, items):
        dialog = QDialog(self.parent)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(label))
        search_field = QLineEdit()
        search_field.setPlaceholderText(_("🔍 Type to filter..."))
        layout.addWidget(search_field)
        list_widget = QListWidget()
        for item in items:
            QListWidgetItem(item, list_widget)
        layout.addWidget(list_widget)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.setLayout(layout)

        def filter_items(text):
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                item.setHidden(text.lower() not in item.text().lower())

        search_field.textChanged.connect(filter_items)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            current_item = list_widget.currentItem()
            if current_item:
                return current_item.text()
        return None

    def show_radio_list_dialog(self, title, label, items):
        dialog = QDialog(self.parent)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(label))
        radio_buttons = []
        for text, enabled in items:
            radio = QRadioButton(text)
            radio.setEnabled(enabled)
            radio_buttons.append(radio)
            layout.addWidget(radio)
        for radio in radio_buttons:
            if radio.isEnabled():
                radio.setChecked(True)
                break
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.setLayout(layout)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            for i, radio in enumerate(radio_buttons):
                if radio.isChecked():
                    return i + 1
        return None

    def show_autocomplete_combo_dialog(self, title, label, items):
        dialog = QDialog(self.parent)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(label))

        combo = QComboBox()
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        combo.setCompleter(combo.completer())
        combo.addItems(items)
        layout.addWidget(combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)
        dialog.resize(400, 100)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            return combo.currentText()
        return None

    def select_backup_folder(self, start_dir):
        dialog = QFileDialog(self.parent)
        dialog.setWindowTitle("Select Backup Folder")
        dialog.setDirectory(start_dir)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        if dialog.exec():
            selected_folders = dialog.selectedFiles()
            if selected_folders:
                return selected_folders[0]
        return None

    def show_config_created(self, config_path):
        msg_box = QMessageBox(self.parent)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle(_("Configuration created"))
        msg_box.setText(_("Config file created at:\n") + config_path)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Close)

        btn_open_file = QPushButton(_("📝 Open File"))
        btn_open_folder = QPushButton(_("📁 Open Folder"))
        msg_box.addButton(btn_open_file, QMessageBox.ButtonRole.ActionRole)
        msg_box.addButton(btn_open_folder, QMessageBox.ButtonRole.ActionRole)

        def open_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(config_path))
            msg_box.close()

        def open_folder():
            folder = os.path.dirname(config_path)
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
            msg_box.close()

        btn_open_file.clicked.connect(open_file)
        btn_open_folder.clicked.connect(open_folder)

        msg_box.exec()
