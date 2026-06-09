#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

missing_pyside6_tools() {
  echo "PySide6 command-line tools not found."
  echo
  echo "Install the project dependencies first:"
  echo "  mamba env create -f environment.yml"
  echo "  conda env create -f environment.yml"
  echo
  echo "Or, using pip:"
  echo "  python -m pip install -r requirements.txt"
  exit 1
}

command -v pyside6-uic >/dev/null || missing_pyside6_tools
command -v pyside6-rcc >/dev/null || missing_pyside6_tools

pyside6-uic mainwindow.ui -o MainWindow.py
pyside6-uic targetdialog.ui -o TargetDialog.py
pyside6-rcc resources.qrc -o resources.py

echo "Generated PySide6 files."