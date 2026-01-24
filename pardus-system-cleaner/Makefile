.PHONY: run build clean install test

PYTHON = python3
MAIN = src/main.py

run:
	@echo "Starting Pardus System Cleaner in DEV mode..."
	export PYTHONPATH=.:$PYTHONPATH && $(PYTHON) $(MAIN)

build:
	@echo "Building Debian package..."
	# Create staging area
	mkdir -p dist/DEBIAN
	mkdir -p dist/usr/share/pardus-system-cleaner/src
	mkdir -p dist/usr/share/pardus-system-cleaner/resources
	mkdir -p dist/usr/bin
	
	# Copy files
	cp debian/control dist/DEBIAN/
	cp -r src/* dist/usr/share/pardus-system-cleaner/src/
	cp -r resources/* dist/usr/share/pardus-system-cleaner/resources/
	cp bin/pardus-system-cleaner dist/usr/bin/
	chmod +x dist/usr/bin/pardus-system-cleaner
	
	# Build
	dpkg-deb --build dist pardus-system-cleaner.deb
	@echo "Package built: pardus-system-cleaner.deb"

clean:
	@echo "Cleaning up..."
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
	rm -f *.deb
	rm -rf dist

test:
	$(PYTHON) -m unittest discover src
