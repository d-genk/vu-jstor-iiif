import requests
import time
import xml.etree.ElementTree as ET

# --- CONFIGURATION ---
BASE_URL = "https://stewardship.jstor.org/oai/"
OUTPUT_FILENAME = "harvested_identifiers.txt"
PARAMETERS = {
    "verb": "ListIdentifiers",
    "set": "56539",
    "metadataPrefix": "oai_dc"
}

# Namespaces are required to parse OAI XML
NAMESPACES = {
    'oai': 'http://www.openarchives.org/OAI/2.0/'
}

def get_all_identifiers():
    current_params = PARAMETERS.copy()
    total_ids = 0
    batch_count = 0
    
    # Session helps maintain connections (like keep-alive)
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    })

    print(f"--- Starting Harvest ---")
    print(f"--- Saving IDs to: {OUTPUT_FILENAME} ---")

    # Open the file in 'write' mode initially to clear it, then we keep it open
    with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
        
        while True:
            batch_count += 1
            print(f"\n--- Fetching Batch {batch_count} ---")
            
            try:
                # 1. Make the request
                response = session.get(BASE_URL, params=current_params)
                response.raise_for_status()
                
                # 2. Parse the XML
                root = ET.fromstring(response.content)
                
                # 3. Find all header identifiers in this batch
                headers = root.findall('.//oai:header', NAMESPACES)
                
                if not headers:
                    print("No identifiers found in this batch.")
                
                batch_ids = 0
                for header in headers:
                    identifier = header.find('oai:identifier', NAMESPACES)
                    if identifier is not None:
                        # Print to console (optional, maybe too noisy if list is huge)
                        # print(f"  {identifier.text}")
                        
                        # Write to file
                        f.write(identifier.text + "\n")
                        batch_ids += 1
                        total_ids += 1
                
                print(f"  > Saved {batch_ids} identifiers to file.")

                # 4. Check for Resumption Token
                token_element = root.find('.//oai:resumptionToken', NAMESPACES)
                
                if token_element is None or not token_element.text:
                    print(f"--- No resumption token found. Harvest complete. ---")
                    break
                
                token = token_element.text
                print(f"  > Token found: {token[:10]}...")
                print(f"  > Total collected so far: {total_ids}")
                
                # 5. Prepare for next loop
                current_params = {
                    "verb": "ListIdentifiers",
                    "resumptionToken": token
                }
                
                # Be polite to the server
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                print(f"HTTP Error: {e}")
                break
            except ET.ParseError as e:
                print(f"XML Parsing Error: {e}")
                print(f"Response content was: {response.text[:500]}")
                break

    print(f"\n--- Finished. Total Identifiers: {total_ids} ---")
    print(f"--- Check {OUTPUT_FILENAME} for results. ---")

if __name__ == "__main__":
    get_all_identifiers()