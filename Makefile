## Maha Claude — Build Targets
##
## Usage:
##   make              Build all components
##   make client       Build maha-client exe (PyInstaller)
##   make gateway      Build maha-gateway Docker image
##   make orchestrator Build maha-orchestrator Docker image
##   make test         Run all tests
##   make clean        Remove build artefacts

PYTHON := python3
DOCKER := docker
IMAGE_TAG := latest

.PHONY: all client gateway orchestrator test clean help

# ── Default ──────────────────────────────────────────────────────────────────
all: gateway orchestrator client

# ── Client (PyInstaller single exe) ─────────────────────────────────────────
client:
	@echo ">>> Building maha-client..."
	bash client/build.sh

# ── Gateway (Docker image) ───────────────────────────────────────────────────
gateway:
	@echo ">>> Building maha-gateway Docker image..."
	$(DOCKER) build \
		--tag maha-gateway:$(IMAGE_TAG) \
		--file gateway/Dockerfile \
		gateway/
	@echo "    Image: maha-gateway:$(IMAGE_TAG)"

# ── Orchestrator (Docker image) ──────────────────────────────────────────────
orchestrator:
	@echo ">>> Building maha-orchestrator Docker image..."
	$(DOCKER) build \
		--tag maha-orchestrator:$(IMAGE_TAG) \
		--file orchestrator/Dockerfile \
		orchestrator/
	@echo "    Image: maha-orchestrator:$(IMAGE_TAG)"

# ── Tests ────────────────────────────────────────────────────────────────────
test:
	@echo ">>> Running tests..."
	PYTHONPATH=client      $(PYTHON) -m pytest client/tests/ -v
	PYTHONPATH=gateway     $(PYTHON) -m pytest gateway/tests/ -v
	PYTHONPATH=orchestrator $(PYTHON) -m pytest orchestrator/tests/ -v

# ── Clean ────────────────────────────────────────────────────────────────────
clean:
	@echo ">>> Cleaning build artefacts..."
	rm -rf client/dist client/build
	$(DOCKER) rmi maha-gateway:$(IMAGE_TAG) maha-orchestrator:$(IMAGE_TAG) 2>/dev/null || true
	@echo "    Done."

# ── Help ─────────────────────────────────────────────────────────────────────
help:
	@grep -E '^## ' Makefile | sed 's/^## //'
