PYTHON ?= python3
APP_NAME := expense
ENTRYPOINT := src/expense.py

.PHONY: build clean

build:
	$(PYTHON) -m PyInstaller --onefile --name $(APP_NAME) --paths src $(ENTRYPOINT)

clean:
	rm -rf build dist *.spec
