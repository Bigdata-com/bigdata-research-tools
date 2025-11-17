import os

# Override environment variables for testing
os.environ.update(
    {
        "BIGDATA_API_KEY": "fake-key",
        "OPENAI_API_KEY": "fake-key",
        "LOG_LEVEL": "ERROR",
    }
)
