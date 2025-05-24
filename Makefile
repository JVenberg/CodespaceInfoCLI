.PHONY: install uninstall help

# Default target
help:
	@echo "Available targets:"
	@echo "  make install   - Install codespaces command to ~/.local/bin"
	@echo "  make uninstall - Remove codespaces command from ~/.local/bin"
	@echo ""
	@echo "Note: Make sure ~/.local/bin is in your PATH"

install:
	@echo "Installing codespaces command..."
	@mkdir -p ~/.local/bin
	@chmod +x codespaces.py
	@ln -sf $(PWD)/codespaces.py ~/.local/bin/codespaces
	@echo "✓ Installed codespaces to ~/.local/bin/codespaces"
	@echo ""
	@if ! echo $$PATH | grep -q "/.local/bin"; then \
		echo "⚠️  Warning: ~/.local/bin is not in your PATH"; \
		echo "Add this line to your shell configuration file:"; \
		echo "  export PATH=\"\$$HOME/.local/bin:\$$PATH\""; \
	fi

uninstall:
	@echo "Uninstalling codespaces command..."
	@rm -f ~/.local/bin/codespaces
	@echo "✓ Removed codespaces from ~/.local/bin"
