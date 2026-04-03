from dotenv import load_dotenv
from fastmcp import FastMCP
import requests
import os

load_dotenv()

EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")

if not EXCHANGE_RATE_API_KEY:
    raise ValueError("EXCHANGE_RATE_API_KEY is not set in the environment variables.")

mcp = FastMCP("Exchange Rate API MCP Server")

EXCHANGE_RATE_BASE_URL = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/pair/"

@mcp.tool
def convert_currency(amount: float, currency_from: str, currency_to: str) -> str:
    """Converts a specified amount of one currency to another currency.

    Args:
        amount: The amount to be converted. Must be a positive float.
        currency_from: The source currency code in 3-letter ISO 4217 format (e.g., USD, EUR).
        currency_to: The target currency code in 3-letter ISO 4217 format (e.g., USD, EUR).

    Returns:
        A string message detailing the conversion result and the used conversion rate.

    Raises:
        requests.HTTPError: If there are errors related to the API request, such as unknown
            currency codes, malformed requests, or exceeded quota.
    """
    response = requests.get(f"{EXCHANGE_RATE_BASE_URL}{currency_from.upper()}/{currency_to.upper()}/{amount}")
    status_code = response.status_code
    data = response.json()
    if data.get("result") == "error":
        error_type = data.get("error-type", "unknown")
        if error_type == "unsupported-code":
            raise requests.HTTPError(f"({status_code}): Unknown currency code: {currency_from.upper()} or {currency_to.upper()}.")
        elif error_type == "malformed-request":
            raise requests.HTTPError(f"({status_code}): Malformed request")
        elif error_type == "invalid-key":
            raise requests.HTTPError(f"({status_code}): Invalid API key")
        elif error_type == "inactive-account":
            raise requests.HTTPError(f"({status_code}): Account inactive")
        elif error_type == "quota-reached":
            raise requests.HTTPError(f"({status_code}): API quota reached. Please try again later.")
        else:
            raise requests.HTTPError(f"({status_code}): API error: {error_type}")

    conversion_result = data.get("conversion_result")
    conversion_rate = data.get("conversion_rate")

    return f"{amount} of {currency_from.upper()} converts to {conversion_result:.2f} {currency_to.upper()} using conversion rate {conversion_rate}"

if __name__ == "__main__":

    # The section is to filter a benign Windows-specific asyncio quirk.
    import asyncio
    import sys

    if sys.platform == "win32":
        # Suppress spurious WinError 10054 on client disconnect.
        # Must use run_async() + loop.run_until_complete() so FastMCP runs on
        # this loop instead of creating a new one via asyncio.run().
        loop = asyncio.ProactorEventLoop()
        def _ignore_connection_reset(loop, context):
            if "WinError 10054" in str(context.get("exception", "")):
                return
            loop.default_exception_handler(context)
        loop.set_exception_handler(_ignore_connection_reset)
        asyncio.set_event_loop(loop)
        loop.run_until_complete(mcp.run_async(transport="streamable-http"))
    else:
        mcp.run(transport="streamable-http")