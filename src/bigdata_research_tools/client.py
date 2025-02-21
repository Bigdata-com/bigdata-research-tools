from logging import Logger, getLogger
from os import environ
from time import sleep
from typing import Optional

from bigdata_client import Bigdata

logger: Logger = getLogger(__name__)

_bigdata_client: Optional[Bigdata] = None


def init_bigdata_client(
    user: str = None,
    password: str = None,
    retries: int = 5,
    wait_time: int = 3,
) -> Bigdata:
    """
    Initialize the BigData client.

    Args:
        user (str): The username to authenticate.
            If None, it will try to get it from the environment variable BIGDATA_USERNAME.
        password (str): The password to authenticate.
            If None, it will try to get it from the environment variable BIGDATA_PASSWORD.
        retries (int): The number of retries to attempt.
        wait_time (int): The time to wait between retries.
    """
    user = user or environ.get("BIGDATA_USERNAME", None)
    password = password or environ.get("BIGDATA_PASSWORD", None)
    file_config = environ.get("BIGDATA_FILE_CONFIG", "Skipped")
    if retries > 0:
        try:
            logger.debug(
                f"Attempting to initialize BigData client.\nFile config: {file_config}"
            )
            client = Bigdata(user, password)
        except Exception as e:
            logger.warning(
                f"Bigdata error: {type(e).__name__}. {e}.\n"
                f"Waiting {wait_time} seconds and retrying...",
            )
            sleep(wait_time)
            return init_bigdata_client(
                user,
                password,
                retries=retries - 1,
                wait_time=wait_time + 1,
            )
    else:
        error_log = "All retries spent trying to initialize Bigdata!"
        logger.error(error_log)
        raise EnvironmentError(error_log)
    return client


def bigdata_connection():
    """
    Get the BigData client, using a singleton pattern.
    """
    global _bigdata_client
    if _bigdata_client is None:
        _bigdata_client = init_bigdata_client()
    return _bigdata_client
