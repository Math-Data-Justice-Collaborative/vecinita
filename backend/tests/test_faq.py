import sys
import os
import logging

# Configure logging to see the internal tool messages
logging.basicConfig(level=logging.INFO)

# Ensure Python can find your 'src' module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.agent.tools.static_response import static_response_tool

def run_test():
    print("--- Starting End-to-End FAQ Test ---\n")

    # The exact query you wanted to test
    test_query = "what is vecinita"
    
    print(f"Input Query: '{test_query}'")
    
    # calling the tool directly
    response = static_response_tool.invoke({"query": test_query})
    
    print(f"\nResult: {response}")
    print("\n--- Test Complete ---")

if __name__ == "__main__":
    run_test()
