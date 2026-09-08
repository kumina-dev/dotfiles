from concurrent.futures import (
    ThreadPoolExecutor,
)

from gi.repository import GLib


_executor = ThreadPoolExecutor(
    max_workers=4,
    thread_name_prefix="kumina",
)


def run_async(
    function,
    callback=None,
    error_callback=None,
):
    future = _executor.submit(
        function
    )

    def finished(future):
        try:
            result = future.result()
        except Exception as error:
            if error_callback:
                GLib.idle_add(
                    error_callback,
                    error,
                )

            return

        if callback:
            GLib.idle_add(
                callback,
                result,
            )

    future.add_done_callback(
        finished
    )

    return future