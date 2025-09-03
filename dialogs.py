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
    QMessageBox,
    QRadioButton,
    QVBoxLayout,
)

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
