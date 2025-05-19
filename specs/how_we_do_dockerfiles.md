# Docker Best Practices for Claude Code Environment

This document outlines our Docker best practices for creating and maintaining the Claude Code isolated environment.

## Layer Ordering for Optimal Caching

When building Docker images, we order layers strategically to maximize cache efficiency:

1. **Base OS & System Packages First**: Start with the base OS image and install system packages that change infrequently.
   ```dockerfile
   FROM archlinux:latest
   RUN pacman -Syu --noconfirm && pacman -S --noconfirm base-devel git ...
   ```

2. **User Setup & Environment Variables**: Set up the non-root user and environment variables.
   ```dockerfile
   RUN useradd -m -s /bin/bash coder
   ENV HOME=/home/coder
   USER coder
   ```

3. **Development Tools & Language Runtimes**: Install language runtimes and development tools.
   ```dockerfile
   RUN rustup update && rustup toolchain install stable ...
   ```

4. **Application-Specific Packages**: Install packages specific to the application.
   ```dockerfile
   RUN npm install -g @anthropic-ai/claude-code
   ```

5. **Configuration Files Last**: Copy configuration files as one of the last steps, as these change frequently.
   ```dockerfile
   COPY docker_configs/dot_bashrc ${HOME}/.bashrc
   ```

This ordering ensures that when we make changes to configurations or application code, we only rebuild the necessary layers, saving build time and resources.

## Environment Variables and Configuration

1. **Pass Secrets via Environment Variables**: Never hardcode secrets in the Dockerfile.
   ```dockerfile
   # In the Dockerfile - just define the environment variable
   ENV ANTHROPIC_API_KEY=""
   
   # When running the container, pass the actual value
   docker run -e ANTHROPIC_API_KEY=your_api_key ...
   ```

2. **Use ARG for Build-Time Variables**: Use ARG for variables needed only during build.
   ```dockerfile
   ARG BUILD_VERSION=latest
   RUN echo "Building version ${BUILD_VERSION}"
   ```

## Security Considerations

1. **Run as Non-Root User**: Always run applications as a non-root user.
   ```dockerfile
   RUN useradd -m -s /bin/bash coder
   USER coder
   ```

2. **Minimize Installed Packages**: Only install what's necessary to reduce attack surface.

3. **Multi-Stage Builds**: Use multi-stage builds for compiled applications to keep final images small.

4. **Container Isolation**: Run containers with appropriate isolation flags:
   ```bash
   docker run --security-opt=no-new-privileges ...
   ```

## Development Workflow

1. **Mount Volumes for Development**: Mount local directories for active development.
   ```bash
   docker run -v $(pwd):/home/coder/workspace ...
   ```

2. **Separate Dev and Prod Configs**: Use different configurations for development and production.

3. **Debugging Tools**: Include debugging tools in development images, but exclude them from production.

## Claude Code Specific Considerations

1. **API Key Handling**: Always pass the Anthropic API key as an environment variable, never hardcode it.

2. **MCP Tools Setup**: Place MCP tools setup scripts in a consistent location (/opt/claude-code).

3. **Workspace Directory**: Maintain a consistent workspace directory structure.

4. **Permissions**: Be mindful of file permissions when copying files from host to container.

## Testing and Validation

1. **Test New Images**: Always test new images with test_in_docker.py before deploying.

2. **Validate MCP Tool Registration**: Ensure MCP tools are properly registered and accessible.

3. **Check Environment Variables**: Verify environment variables are correctly passed and accessible.