import gettext
from PyQt6.QtCore import Qt, QTimer
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

_ = gettext.gettext


class Dialogs:
    def __init__(self, parent=None):
        self.parent = parent

    # Create base dialog with layout and standard buttons
    def _create_base_dialog(self, title, buttons=QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel):
        dialog = QDialog(self.parent)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout(dialog)
        btn_box = QDialogButtonBox(buttons)
        layout.addWidget(btn_box)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        dialog.setLayout(layout)
        return dialog, layout, btn_box

    # Add a custom button with callback to button box
    def _add_custom_button(self, btn_box, text, role, callback):
        btn = QPushButton(text)
        btn_box.addButton(btn, role)
        btn.clicked.connect(callback)
        return btn

    # Generic dialog to show message with configurable buttons
    def show_custom_dialog(self, title, message, buttons_callbacks=None, rich_text=True,
                           interaction_flags=Qt.TextInteractionFlag.TextBrowserInteraction):
        dialog, layout, btn_box = self._create_base_dialog(title, QDialogButtonBox.StandardButton.Close)

        label = QLabel(message)
        if rich_text:
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setTextInteractionFlags(interaction_flags)
            label.setOpenExternalLinks(True)
        else:
            label.setTextFormat(Qt.TextFormat.PlainText)

        layout.insertWidget(0, label)

        if buttons_callbacks:
            for btn_text, callback in buttons_callbacks:
                self._add_custom_button(btn_box, btn_text, QDialogButtonBox.ButtonRole.ActionRole, callback)

        dialog.exec()

    # Simple message box with OK button
    def show_message_box(self, text, title="PyWebSearch", icon=QMessageBox.Icon.Information):
        msg = QMessageBox(self.parent)
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    # Yes/No question dialog
    def show_yes_no_box(self, text, title="PyWebSearch", default_button=QMessageBox.StandardButton.No):
        reply = QMessageBox.question(
            self.parent,
            title,
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            default_button,
        )
        return reply == QMessageBox.StandardButton.Yes

    # Input text dialog
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

    # List dialog (combo or radio buttons)
    def show_list_dialog(self, title, label, items, radio=False):
        dialog, layout, btn_box = self._create_base_dialog(title)
        layout.insertWidget(0, QLabel(label))

        if radio:
            radio_buttons = []
            for i, (text, checked) in enumerate(items):
                radio_button = QRadioButton(text)
                radio_button.setChecked(checked)
                layout.insertWidget(layout.count() - 1, radio_button)
                radio_buttons.append((str(i + 1), radio_button))
            if dialog.exec() == QDialog.DialogCode.Accepted:
                for val, button in radio_buttons:
                    if button.isChecked():
                        return val
        else:
            combo = QComboBox()
            combo.addItems(items)
            layout.insertWidget(0, combo)
            result = None
            if dialog.exec() == QDialog.DialogCode.Accepted:
                result = combo.currentText()
            return result
        return None

    # Searchable list dialog
    def show_searchable_list_dialog(self, title, label, items):
        dialog, layout, btn_box = self._create_base_dialog(title)
        layout.insertWidget(0, QLabel(label))

        search_field = QLineEdit()
        search_field.setPlaceholderText(_("🔍 Type to filter..."))
        layout.insertWidget(1, search_field)

        list_widget = QListWidget()
        for item in items:
            QListWidgetItem(item, list_widget)
        layout.insertWidget(2, list_widget)

        def filter_items(text):
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                item.setHidden(text.lower() not in item.text().lower())

        search_field.textChanged.connect(filter_items)

        # Connect double-click signal to accept dialog and close
        def item_double_clicked(item):
            # Select the double-clicked item explicitly (usually already selected)
            list_widget.setCurrentItem(item)
            dialog.accept()

        list_widget.itemDoubleClicked.connect(item_double_clicked)

        selected_text = None
        if dialog.exec() == QDialog.DialogCode.Accepted:
            current_item = list_widget.currentItem()
            if current_item:
                selected_text = current_item.text()

        return selected_text

    # Radio button list dialog
    def show_radio_list_dialog(self, title, label, items):
        dialog, layout, btn_box = self._create_base_dialog(title)
        layout.insertWidget(0, QLabel(label))

        radio_buttons = []
        for text, enabled in items:
            radio = QRadioButton(text)
            radio.setEnabled(enabled)
            layout.insertWidget(layout.count() - 1, radio)
            radio_buttons.append(radio)

        for radio in radio_buttons:
            if radio.isEnabled():
                radio.setChecked(True)
                break

        selected_index = None
        if dialog.exec() == QDialog.DialogCode.Accepted:
            for i, radio in enumerate(radio_buttons):
                if radio.isChecked():
                    selected_index = i + 1

        return selected_index

    # Autocomplete combo box dialog
    def show_autocomplete_combo_dialog(self, title, label, items):
        dialog, layout, btn_box = self._create_base_dialog(title)
        layout.insertWidget(0, QLabel(label))

        combo = QComboBox()
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        combo.setCompleter(combo.completer())
        combo.addItems(items)
        layout.insertWidget(1, combo)

        dialog.resize(400, 100)

        selected_text = None
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_text = combo.currentText()

        return selected_text

    # Directory selection dialog
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

    # Backup created dialog with clickable path and 'Open Folder' button
    def show_backup_created(self, backup_folder_path, message=None):
        if message is None:
            message = f'Backup created at:<br><a href="file://{backup_folder_path}">{backup_folder_path}</a>'
        else:
            message = f'{message}<br><a href="file://{backup_folder_path}">{backup_folder_path}</a>'

        def open_folder():
            QDesktopServices.openUrl(QUrl.fromLocalFile(backup_folder_path))
            QTimer.singleShot(300, lambda: None)

        self.show_custom_dialog(
            "Backup Created",
            message,
            buttons_callbacks=[("📁 Open Folder", open_folder)]
        )
