import os
import redis
import time
import zipfile
import importlib.util
import json
import logging
import sys
from pathlib import Path

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class RuntimeEnvironment:
    def __init__(self, config):
        self.config = config

def extract_and_load_function(zip_archive, entry_file, target_function):
    work_dir = "/tmp/runtime_code"
    try:
        with zipfile.ZipFile(zip_archive, "r") as archive:
            archive.extractall(work_dir)
        script_path = os.path.join(work_dir, entry_file)
        if not os.path.isfile(script_path):
            raise FileNotFoundError(f"Entry script '{entry_file}' not found in ZIP.")
        spec = importlib.util.spec_from_file_location("runtime_module", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if not hasattr(module, target_function):
            raise AttributeError(f"Function '{target_function}' not defined in '{entry_file}'.")
        return getattr(module, target_function)
    except Exception as err:
        logging.error(f"Failed to load function from ZIP: {err}")
        raise
    finally:
        if os.path.exists(work_dir):
            for root, _, files in os.walk(work_dir, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                os.rmdir(root)

def load_function_from_file(script_path, target_function):
    try:
        if not Path(script_path).exists():
            raise FileNotFoundError(f"Script file '{script_path}' not found.")
        sys.path.append(os.path.dirname(script_path))
        spec = importlib.util.spec_from_file_location("runtime_module", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if not hasattr(module, target_function):
            raise AttributeError(f"Function '{target_function}' not found in '{script_path}'.")
        return getattr(module, target_function)
    except Exception as err:
        logging.error(f"Failed to load function from file: {err}")
        raise

def initialize_handler(source_type, script_path, zip_archive, entry_file, function_name):
    if source_type == "file":
        return load_function_from_file(script_path, function_name)
    elif source_type == "zip":
        return extract_and_load_function(zip_archive, entry_file, function_name)
    else:
        raise ValueError("Invalid source type: Must be 'file' or 'zip'.")

def handle_event(handler, event_data, redis_instance, output_channel, runtime_context):
    try:
        output = handler(event_data, runtime_context)
        if isinstance(output, dict):
            redis_instance.set(output_channel, json.dumps(output))
            logging.info(f"Result stored in Redis under key '{output_channel}'")
        else:
            logging.warning("Handler did not return a dictionary. Output ignored.")
    except Exception as err:
        logging.error(f"Error while processing event: {err}")

def start_runtime():
    redis_host = os.getenv("RUNTIME_REDIS_HOST", "localhost")
    redis_port = int(os.getenv("RUNTIME_REDIS_PORT", 6379))
    input_channel = os.getenv("RUNTIME_INPUT_CHANNEL", "events")
    output_channel = os.getenv("RUNTIME_OUTPUT_CHANNEL", "results")
    polling_interval = int(os.getenv("RUNTIME_POLL_INTERVAL", 5))
    source_type = os.getenv("RUNTIME_SOURCE_TYPE", "file")
    script_path = os.getenv("RUNTIME_SCRIPT_PATH", "/code/mymodule.py")
    zip_archive = os.getenv("RUNTIME_ZIP_PATH", "/code/function.zip")
    entry_file = os.getenv("RUNTIME_ZIP_ENTRY", "mymodule.py")
    function_name = os.getenv("RUNTIME_FUNCTION_NAME", "handler")

    try:
        redis_instance = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        redis_instance.ping()
        logging.info(f"Connected to Redis at {redis_host}:{redis_port}")
    except redis.ConnectionError as err:
        logging.error(f"Unable to connect to Redis: {err}")
        return

    try:
        handler = initialize_handler(source_type, script_path, zip_archive, entry_file, function_name)
    except Exception as err:
        logging.error(f"Error loading handler: {err}")
        return

    context = RuntimeEnvironment(config={})
    previous_event = None

    while True:
        try:
            event = redis_instance.get(input_channel)
            if event:
                event_data = json.loads(event)
                if event_data != previous_event:
                    logging.info("Processing new event...")
                    previous_event = event_data
                    handle_event(handler, event_data, redis_instance, output_channel, context)
                else:
                    logging.debug("No new events detected.")
            else:
                logging.info(f"No data found on input channel '{input_channel}'")
        except json.JSONDecodeError as err:
            logging.error(f"JSON decode error: {err}")
        except Exception as err:
            logging.error(f"Error processing Redis data: {err}")
        time.sleep(polling_interval)

if __name__ == "__main__":
    start_runtime()
