# Dockerfile for Claude Code isolated environment
# Base image: Arch Linux (latest)
FROM archlinux:latest

# Set environment variables
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US
ENV LC_ALL=en_US.UTF-8
ENV HOME=/home/coder
ENV PATH="${HOME}/.npm-global/bin:${HOME}/.cargo/bin:${HOME}/.local/bin:${PATH}"
ENV npm_config_prefix="${HOME}/.npm-global"

# Install base development tools and packages
# Notes:
# - base-devel provides essential build tools
# - tmux, vim, and git for development
# - python, nodejs, and rust for language support
# - yarn and npm for JavaScript/TypeScript development
# - For any missing packages, add them to this list in future iterations
RUN pacman -Syu --noconfirm && \
    pacman -S --noconfirm \
    base-devel \
    git \
    vim \
    tmux \
    python \
    python-pip \
    rustup \
    nodejs \
    npm \
    yarn \
    semver \
    nodejs-nopt \
    curl \
    wget \
    tar \
    gzip \
    unzip \
    which \
    net-tools \
    procps-ng \
    sudo

# Create a non-root user for running Claude Code
RUN useradd -m -s /bin/bash coder && \
    echo "coder ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/coder && \
    chmod 0440 /etc/sudoers.d/coder

# Switch to the non-root user for the remaining steps
USER coder
WORKDIR ${HOME}

# Set up Rust
RUN rustup update && \
    rustup toolchain install stable && \
    rustup default stable

# Set up npm global directory
RUN mkdir -p ${HOME}/.npm-global && \
    npm config set prefix "${HOME}/.npm-global"

# Install uv package manager for Python
RUN curl -sSf https://astral.sh/uv/install.sh | sh

# Install Claude Code globally with npm
# This step is done late in the build process to utilize Docker caching
# If Claude Code package updates, only this layer and subsequent ones will rebuild
RUN npm install -g @anthropic-ai/claude-code

# Create workspace directory
RUN mkdir -p ${HOME}/workspace

# Copy dot_bashrc from host to container
COPY --chown=coder:coder docker_configs/dot_bashrc ${HOME}/.bashrc

# Copy MCP tool setup script
RUN mkdir -p /opt/claude-code
COPY --chown=coder:coder docker_configs/setup_mcp_tool.py /opt/claude-code/

# Set entrypoint and default command
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["cd ${HOME}/workspace && /bin/bash -l"]

# Keep container running if needed for debugging
# CMD ["tail", "-f", "/dev/null"]