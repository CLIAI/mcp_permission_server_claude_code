# MCP Permission Server - WIP

**WORK IN PROGRESS**: This repository contains experimental code for implementing custom security policies for Claude Code MCP (Model Control Panel) tools.

## Purpose

This project aims to develop minimal working examples for MCP tool approval/denial servers that could serve as a foundation for implementing security policies to control Claude Code's capabilities. The goal is to create simple examples ranging from:

- Basic "always allow/deny" servers
- Pattern matching (regex-based) permission controllers
- More complex permission management systems

## Current Status

⚠️ **WARNING**: Currently non-functional due to lack of clear documentation and examples.

Despite attempts to create even minimal "hello world" examples for permission servers, the author encountered significant challenges with:
- Insufficient documentation on MCP permission server implementation
- Lack of working examples to reference
- Unclear error handling and debugging procedures

This repository is being published to:
1. Share current progress with the community
2. Help others reproduce the issues encountered
3. Potentially collaborate on solutions

## Directory Structure

The repository contains several experimental implementations using different frameworks:
- `mcp_permission_server_allow_always_fastmcp`: Simple FastAPI implementation intended to always allow tool use
- `mcp_permission_server_fastmcp_another`: Alternative FastAPI implementation
- `mcp_permission_server_fastmcp_with_typing`: FastAPI with explicit type definitions
- `mcp_permission_server_genai_by_gemini`: Implementation using Gemini
- `mcp_permission_server_genai_by_gemini_another`: Alternative Gemini implementation
- `mcp_permission_server_genai_by_perplexity`: Implementation using Perplexity
- `mcp_permission_server_return_json_string`: Simple server returning JSON strings

## Future Work

The plan is to add:
- Dockerfiles for containerized testing of each implementation
- A Makefile to simplify reproduction of issues encountered
- Better documentation based on findings

## Contributing

If you have insights on how to make these examples work or have successfully implemented an MCP permission server, please open an issue or submit a pull request with your findings.

## License

See the [LICENSE](LICENSE) file for details.