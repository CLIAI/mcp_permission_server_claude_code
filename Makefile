# Makefile for Claude Code Docker environment

# Variables
IMAGE_NAME = claude-code-container
CONTAINER_NAME = claude-code
DOCKER_FILE = Dockerfile

# Default target when 'make' is run without arguments
.PHONY: all
all: build

# Build the Docker image
.PHONY: build
build:
	@echo "Building Docker image: $(IMAGE_NAME)"
	docker build -t $(IMAGE_NAME) -f $(DOCKER_FILE) .

# Run a container interactively with the current directory mounted
.PHONY: run
run:
	@echo "Running interactive container with current directory mounted"
	@if [ -z "$$ANTHROPIC_API_KEY" ]; then \
		echo "Error: ANTHROPIC_API_KEY environment variable is not set"; \
		echo "Set your API key with: export ANTHROPIC_API_KEY=your_api_key_here"; \
		exit 1; \
	fi
	docker run --rm -it \
		-v $(shell pwd):/home/coder/workspace \
		-e ANTHROPIC_API_KEY \
		--name $(CONTAINER_NAME) \
		$(IMAGE_NAME)

# Run a container in the background
.PHONY: run-daemon
run-daemon:
	@echo "Running container in background with current directory mounted"
	@if [ -z "$$ANTHROPIC_API_KEY" ]; then \
		echo "Error: ANTHROPIC_API_KEY environment variable is not set"; \
		echo "Set your API key with: export ANTHROPIC_API_KEY=your_api_key_here"; \
		exit 1; \
	fi
	docker run -d \
		-v $(shell pwd):/home/coder/workspace \
		-e ANTHROPIC_API_KEY \
		--name $(CONTAINER_NAME) \
		$(IMAGE_NAME) "tail -f /dev/null"

# Enter a running container
.PHONY: shell
shell:
	@echo "Entering shell in running container"
	@if ! docker ps -q --filter "name=$(CONTAINER_NAME)" | grep -q .; then \
		echo "Container $(CONTAINER_NAME) is not running. Starting..."; \
		make run-daemon; \
	fi
	docker exec -it $(CONTAINER_NAME) /bin/bash

# Stop a running container
.PHONY: stop
stop:
	@echo "Stopping container if running"
	@if docker ps -q --filter "name=$(CONTAINER_NAME)" | grep -q .; then \
		docker stop $(CONTAINER_NAME); \
	else \
		echo "Container $(CONTAINER_NAME) is not running"; \
	fi

# Remove a container (stops it first if necessary)
.PHONY: rm
rm: stop
	@echo "Removing container if it exists"
	@if docker ps -a -q --filter "name=$(CONTAINER_NAME)" | grep -q .; then \
		docker rm $(CONTAINER_NAME); \
	else \
		echo "Container $(CONTAINER_NAME) does not exist"; \
	fi

# Remove the Docker image
.PHONY: rmi
rmi: rm
	@echo "Removing Docker image if it exists"
	@if docker images $(IMAGE_NAME) | grep -q $(IMAGE_NAME); then \
		docker rmi $(IMAGE_NAME); \
	else \
		echo "Image $(IMAGE_NAME) does not exist"; \
	fi

# Clean everything (remove container and image)
.PHONY: clean
clean: rmi
	@echo "Clean completed"

# Run a test script using the test_in_docker.py helper
.PHONY: test-script
test-script:
	@if [ -z "$(SCRIPT)" ]; then \
		echo "Error: SCRIPT variable is not set"; \
		echo "Usage: make test-script SCRIPT=path/to/your/script.py"; \
		exit 1; \
	fi
	@if [ -z "$$ANTHROPIC_API_KEY" ]; then \
		echo "Error: ANTHROPIC_API_KEY environment variable is not set"; \
		echo "Set your API key with: export ANTHROPIC_API_KEY=your_api_key_here"; \
		exit 1; \
	fi
	@echo "Testing script: $(SCRIPT)"
	./test_in_docker.py $(SCRIPT)

# Help target
.PHONY: help
help:
	@echo "Claude Code Docker Environment Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  build        - Build the Docker image"
	@echo "  run          - Run an interactive container with current directory mounted"
	@echo "  run-daemon   - Run a container in the background"
	@echo "  shell        - Enter a shell in a running container"
	@echo "  stop         - Stop a running container"
	@echo "  rm           - Remove a container (stops it first if necessary)"
	@echo "  rmi          - Remove the Docker image (removes container first)"
	@echo "  clean        - Remove container and image"
	@echo "  test-script  - Test a script using test_in_docker.py helper"
	@echo "                 Usage: make test-script SCRIPT=path/to/your/script.py"
	@echo "  help         - Show this help message"
	@echo ""
	@echo "Note: ANTHROPIC_API_KEY environment variable must be set for most targets"