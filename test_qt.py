import sys
from PyQt5.QtWidgets import QApplication, QFormLayout, QWidget, QLineEdit
app = QApplication(sys.argv)
w = QWidget()
l = QFormLayout(w)
e = QLineEdit()
l.addRow("Test:", e)
lbl = l.labelForField(e)
print("Label found:", lbl is not None)
