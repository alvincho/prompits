from prompits.services.Ollama import Ollama
from prompits.Practice import Practice
from prompits.Pit import Pit
from prompits.services.Service import Service
from prompits.services.APIService import APIService
from prompits.services.LLM import LLM

# Create an Ollama instance
ollama = Ollama("ollama", "Test Ollama", default_model="llama3")

# Print the practices
print(f"Ollama practices: {list(ollama.practices.keys())}")

# Test ToJson on each inheritance level
pit_json = Pit.ToJson(ollama)
service_json = Service.ToJson(ollama)
api_service_json = APIService.ToJson(ollama)
llm_json = LLM.ToJson(ollama)
ollama_json = ollama.ToJson()

# Check for practices at each level
print("\nPractices in JSON representations:")
print(f"Pit.ToJson - practices included: {'practices' in pit_json}")
if 'practices' in pit_json:
    print(f"  Count: {len(pit_json['practices'])}")
    print(f"  Keys: {list(pit_json['practices'].keys())}")

print(f"Service.ToJson - practices included: {'practices' in service_json}")
if 'practices' in service_json:
    print(f"  Count: {len(service_json['practices'])}")
    print(f"  Keys: {list(service_json['practices'].keys())}")

print(f"APIService.ToJson - practices included: {'practices' in api_service_json}")
if 'practices' in api_service_json:
    print(f"  Count: {len(api_service_json['practices'])}")
    print(f"  Keys: {list(api_service_json['practices'].keys())}")

print(f"LLM.ToJson - practices included: {'practices' in llm_json}")
if 'practices' in llm_json:
    print(f"  Count: {len(llm_json['practices'])}")
    print(f"  Keys: {list(llm_json['practices'].keys())}")

print(f"Ollama.ToJson - practices included: {'practices' in ollama_json}")
if 'practices' in ollama_json:
    print(f"  Count: {len(ollama_json['practices'])}")
    print(f"  Keys: {list(ollama_json['practices'].keys())}")

# Print the entire JSON for inspection
print("\nFull Ollama.ToJson():")
import json
print(json.dumps(ollama_json, indent=2)) 