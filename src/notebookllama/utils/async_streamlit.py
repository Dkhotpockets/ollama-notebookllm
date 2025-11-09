"""
Async utilities for Streamlit compatibility
Provides synchronous wrappers for async operations
"""

import asyncio
import sys
from typing import Any, Callable, Awaitable
import concurrent.futures


def run_async(coro: Awaitable[Any]) -> Any:
    """
    Run an async coroutine in a synchronous context (Streamlit compatible)

    This handles the different scenarios:
    - When there's no event loop
    - When there's an existing event loop
    - Windows-specific event loop policies
    """
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Event loop is already running (e.g., in Streamlit)
            # Use ThreadPoolExecutor to run the coroutine
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result(timeout=30)  # 30 second timeout
        else:
            # Event loop exists but not running
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop exists, create one
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        return asyncio.run(coro)


def async_to_sync(async_func: Callable[..., Awaitable[Any]]) -> Callable[..., Any]:
    """
    Decorator to convert async functions to sync functions for Streamlit

    Usage:
        @async_to_sync
        async def my_async_function(arg1, arg2):
            return await some_async_operation(arg1, arg2)

        # Can now be called synchronously
        result = my_async_function(arg1, arg2)
    """
    def sync_wrapper(*args, **kwargs):
        coro = async_func(*args, **kwargs)
        return run_async(coro)
    return sync_wrapper


class AsyncStreamlitHelper:
    """Helper class for async operations in Streamlit"""

    @staticmethod
    def run_async_operation(operation: Callable[[], Awaitable[Any]], timeout: int = 30) -> Any:
        """Run an async operation with timeout"""
        async def wrapper():
            return await operation()

        return run_async(wrapper())

    @staticmethod
    def create_async_callback(async_func: Callable[..., Awaitable[Any]]) -> Callable[..., Any]:
        """Create a synchronous callback from an async function"""
        def callback(*args, **kwargs):
            coro = async_func(*args, **kwargs)
            return run_async(coro)
        return callback