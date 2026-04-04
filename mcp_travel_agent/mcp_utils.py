import asyncio
from mcp.shared.exceptions import McpError
from mcp.types import CallToolResult, TextContent

RETRYABLE_MCP_CODES = {-32603}

class McpRetryInterceptor:
    """Intercept MCP tool calls: retry transient failures, surface all errors gracefully

    - Retryable McpError codes (e.g. -32603): retry with exponential backoff.
    - Non-retryable McpError codes (e.g. -32602): return error message immediately.
    - Any other exception (fetch failed, network errors, etc.): retry then return error message if still failing.
    """

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    async def __call__(self, request, handler):
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return await handler(request)
            except McpError as ex:
                last_error = ex
                if ex.error.code not in RETRYABLE_MCP_CODES:
                    print(f"[MCP interceptor] {type(ex).__name__} on {request.name} "
                          f"(code {ex.error.code}, non-retryable): {ex}")
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"Tool call failed (non-retryable): {ex}")],
                        isError=False
                    )
                print(f"[MCP interceptor] {type(ex).__name__} on {request.name} "
                      f"(code {ex.error.code}, attempt {attempt + 1} of {self.max_retries}): {ex}")
            except Exception as ex:
                last_error = ex
                print(f"[MCP interceptor] {type(ex).__name__} on {request.name} "
                      f"(attempt {attempt + 1} of {self.max_retries}): {ex}")

            if attempt < self.max_retries - 1:
                await asyncio.sleep(2 ** attempt)

        print(f"[MCP interceptor] all {self.max_retries} retries exhausted for {request.name}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Tool call failed after {self.max_retries} attempts: {last_error}")],
            isError=False
        )