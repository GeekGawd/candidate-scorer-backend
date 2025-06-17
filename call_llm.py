from google import genai
import os
import logging
import json
from datetime import datetime
from decouple import config

# Configure logging
log_directory = config("LOG_DIR", default="logs")
os.makedirs(log_directory, exist_ok=True)
log_file = os.path.join(
    log_directory, f"llm_calls_{datetime.now().strftime('%Y%m%d')}.log"
)

# Set up logger
logger = logging.getLogger("llm_logger")
logger.setLevel(logging.INFO)
logger.propagate = False  # Prevent propagation to root logger
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(file_handler)

# Simple cache configuration
cache_file = "llm_cache.json"


def call_llm(prompt: str, use_cache: bool = True) -> str:
    # Log the prompt
    logger.info(f"PROMPT: {prompt}")

    # Check cache if enabled
    if use_cache:
        # Load cache from disk
        cache = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    cache = json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Failed to decode JSON from cache file {cache_file}, starting with empty cache")
                cache = {} # Initialize cache if loading failed
            except IOError as e:
                logger.warning(f"Failed to read cache file {cache_file}: {e}, starting with empty cache")
                cache = {} # Initialize cache if loading failed
            except Exception as e: # Catch any other unexpected error during cache load
                logger.warning(f"An unexpected error occurred while loading cache from {cache_file}: {e}, starting with empty cache")
                cache = {} # Initialize cache

        # Return from cache if exists
        if prompt in cache:
            logger.info(f"RESPONSE: {cache[prompt]}")
            return cache[prompt]


    # You can comment the previous line and use the AI Studio key instead:
    client = genai.Client(
        api_key=config("GEMINI_API_KEY", default=""),
    )
    model = config("GEMINI_MODEL", default="gemini-2.5-pro-exp-03-25")
    # model = config("GEMINI_MODEL", default="gemini-2.5-flash-preview-04-17")
    
    response = client.models.generate_content(model=model, contents=[prompt])
    response_text = response.text

    # Log the response
    logger.info(f"RESPONSE: {response_text}")

    # Update cache if enabled
    if use_cache:
        # Load cache again to avoid overwrites from concurrent processes (if any)
        # Though for a typical script, this might be overkill, but good practice.
        current_cache_on_disk = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    current_cache_on_disk = json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Failed to decode JSON from {cache_file} before saving. New data will overwrite.")
            except IOError as e:
                logger.warning(f"IOError reading {cache_file} before saving: {e}. New data will overwrite.")
            except Exception as e: # Catch any other unexpected error
                logger.warning(f"Unexpected error loading {cache_file} before saving: {e}. New data will overwrite.")

        # Add to cache and save
        current_cache_on_disk[prompt] = response_text # Add or update the current prompt's response
        try:
            with open(cache_file, "w") as f:
                json.dump(current_cache_on_disk, f, indent=4) # Save with indent for readability
        except IOError as e:
            logger.error(f"IOError: Failed to save cache to {cache_file}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: Failed to save cache to {cache_file}: {e}")

    return response_text

if __name__ == "__main__":
    test_prompt = "Hello, how are you?"

    # First call - should hit the API
    print("Making call...")
    response1 = call_llm(test_prompt, use_cache=False)
    print(f"Response: {response1}")