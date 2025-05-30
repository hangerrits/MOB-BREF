# /home/ubuntu/bat_rie_checker/core_logic/llm_handler.py

import openai
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure the OpenAI API key is set as an environment variable
# openai.api_key = os.getenv("OPENAI_API_KEY")
# For newer versions of the openai library, a client is instantiated:
client = openai.OpenAI()

def llm_call(prompt: str, model: str = "gpt-3.5-turbo") -> str | None:
    """Generic function to call the OpenAI LLM."""
    try:
        # Check if API key is available
        if not os.getenv("OPENAI_API_KEY"):
            error_msg = "OpenAI API key (OPENAI_API_KEY) not found in environment variables."
            print(f"ERROR: {error_msg}")
            return f"Error: {error_msg}"

        messages = [{"role": "user", "content": prompt}]
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2 # Lower temperature for more deterministic output
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return f"Error: {e}"

def determine_applicable_brefs(permit_activity_description: str, bref_scopes: list[dict]) -> list[dict]:
    """
    Uses LLM to determine which BREF documents are applicable based on permit activities.

    Args:
        permit_activity_description: Text describing activities in the permit.
        bref_scopes: A list of dictionaries, each containing bref_id and scope_description.
                     Example: [{"bref_id": "BREF1", "scope_description": "Scope of BREF1..."}, ...]

    Returns:
        A list of dictionaries with bref_id, applicability (Likely Applicable, Potentially Applicable, Not Applicable), and justification.
        Example: [{"bref_id": "BREF1", "applicability": "Likely Applicable", "justification": "..."}, ...]
    """
    results = []
    if not bref_scopes:
        return results

    for bref in bref_scopes:
        prompt = f"""
        You are an expert in EU environmental regulations, specifically concerning BREF documents for industrial activities.
        An industrial permit describes the following activities: "{permit_activity_description}"
        A BREF document (ID: {bref['bref_id']}) has the following scope: "{bref['scope_description']}"

        Based on this information, is this BREF document applicable to the described permit activities?
        Classify the applicability as one of: 'Likely Applicable', 'Potentially Applicable', or 'Not Applicable'.
        Provide a brief justification for your classification, referencing specific parts of the permit activities and the BREF scope if possible.
        
        Return your answer in JSON format with the following keys: "bref_id", "applicability", "justification".
        Example JSON response:
        {{
          "bref_id": "{bref['bref_id']}",
          "applicability": "Likely Applicable",
          "justification": "The permit activities fall directly within the scope of this BREF because..."
        }}
        """
        
        print(f"--- Sending prompt to LLM for BREF ID: {bref['bref_id']} Scope Matching ---")
        # print(f"Prompt: {prompt[:500]}...") # Print a snippet of the prompt for brevity
        llm_response_str = llm_call(prompt)
        print(f"LLM Raw Response for {bref['bref_id']}: {llm_response_str}")

        if llm_response_str and not llm_response_str.startswith("Error:"):
            try:
                # Attempt to find JSON within the response, as LLMs can sometimes add extra text
                json_start = llm_response_str.find('{')
                json_end = llm_response_str.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_part = llm_response_str[json_start:json_end]
                    response_json = json.loads(json_part)
                    # Ensure the bref_id from the response matches the one in the prompt
                    if response_json.get("bref_id") == bref["bref_id"]:
                        results.append(response_json)
                    else:
                        print(f"Warning: Mismatched bref_id in LLM response for {bref['bref_id']}. Got {response_json.get('bref_id')}")
                        # Fallback to a structured error if ID mismatch
                        results.append({
                            "bref_id": bref['bref_id'], 
                            "applicability": "Error in LLM Response", 
                            "justification": f"LLM response parsing error or ID mismatch. Raw: {llm_response_str}"
                        })
                else:
                    raise json.JSONDecodeError("No JSON object found", llm_response_str, 0)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from LLM response for {bref['bref_id']}: {e}. Raw response: {llm_response_str}")
                results.append({"bref_id": bref['bref_id'], "applicability": "Error", "justification": f"Failed to parse LLM response: {llm_response_str}"})
        else:
            results.append({"bref_id": bref['bref_id'], "applicability": "Error", "justification": llm_response_str or "No response from LLM"})
    
    return results

def verify_permit_compliance_with_bat(permit_full_text: str, bat_conclusion: dict) -> dict:
    """
    Uses LLM to verify if permit conditions comply with a specific BAT conclusion.

    Args:
        permit_full_text: The full text of the permit (preferably in Markdown).
        bat_conclusion: A dictionary representing a single BAT conclusion, including 
                        `bat_id`, `bat_text_description`, and `source_metadata` (page/paragraph).

    Returns:
        A dictionary with bat_id, compliance_status, and detailed_findings.
        Compliance status can be: 'Compliant', 'Partially Compliant', 'Non-Compliant', 'Ambiguous/Insufficient Information', 'Error'.
    """
    prompt = f"""
    You are an expert in EU environmental regulations and industrial permits.
    You need to meticulously compare the conditions in an industrial permit against a specific Best Available Technique (BAT) conclusion.

    The BAT Conclusion (ID: {bat_conclusion['bat_id']}) is as follows:
    {bat_conclusion['bat_text_description']}
    (Source: BREF Document, Page: {bat_conclusion['source_metadata'].get('page_number', 'N/A')}, Paragraph: {bat_conclusion['source_metadata'].get('paragraph_id', 'N/A')})

    The full text of the industrial permit is provided below (in Markdown format):
    --- PERMIT START ---
    {permit_full_text}
    --- PERMIT END ---

    Analyze the permit text and determine the compliance status with the given BAT conclusion.
    Report on the following aspects, providing specific citations (text snippets with page/paragraph numbers if available in the permit text) from the permit where possible:
    1.  **Compliance:** Is the permit fully compliant with this BAT conclusion? Cite permit text.
    2.  **Partial Compliance/Discrepancies:** Are there any partial compliances or discrepancies? Detail each, citing permit text and the relevant part of the BAT.
    3.  **Non-Compliance/Missing Elements:** Are there any clear non-compliances or missing elements in the permit regarding this BAT? List them.
    4.  **Ambiguity/Insufficient Information:** Are there parts of the BAT that cannot be verified due to ambiguity or insufficient information in the permit? Specify what information is missing.

    Based on your analysis, determine an overall compliance status from the following options: 'Compliant', 'Partially Compliant', 'Non-Compliant', 'Ambiguous/Insufficient Information'.

    Return your answer in JSON format with the following keys: "bat_id", "compliance_status", "detailed_findings".
    The "detailed_findings" should be a textual explanation covering the points above.
    
    Example JSON response:
    {{
      "bat_id": "{bat_conclusion['bat_id']}",
      "compliance_status": "Partially Compliant",
      "detailed_findings": "The permit addresses aspect X of the BAT conclusion (see Permit Page Y, Para Z: '...text...'). However, aspect W is not mentioned, and aspect V is only partially covered (Permit Page A, Para B: '...text...'). Therefore, additional information or clarification is needed for aspect W."
    }}
    """

    print(f"--- Sending prompt to LLM for BAT ID: {bat_conclusion['bat_id']} Compliance Verification ---")
    llm_response_str = llm_call(prompt)
    print(f"LLM Raw Response for {bat_conclusion['bat_id']}: {llm_response_str}")

    if llm_response_str and not llm_response_str.startswith("Error:"):
        try:
            json_start = llm_response_str.find('{')
            json_end = llm_response_str.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_part = llm_response_str[json_start:json_end]
                response_json = json.loads(json_part)
                if response_json.get("bat_id") == bat_conclusion["bat_id"]:
                    return response_json
                else:
                    print(f"Warning: Mismatched bat_id in LLM response for {bat_conclusion['bat_id']}. Got {response_json.get('bat_id')}")
                    return {
                        "bat_id": bat_conclusion['bat_id'], 
                        "compliance_status": "Error in LLM Response", 
                        "detailed_findings": f"LLM response parsing error or ID mismatch. Raw: {llm_response_str}"
                    }
            else:
                raise json.JSONDecodeError("No JSON object found", llm_response_str, 0)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from LLM response for {bat_conclusion['bat_id']}: {e}. Raw response: {llm_response_str}")
            return {"bat_id": bat_conclusion['bat_id'], "compliance_status": "Error", "detailed_findings": f"Failed to parse LLM response: {llm_response_str}"}
    else:
        return {"bat_id": bat_conclusion['bat_id'], "compliance_status": "Error", "detailed_findings": llm_response_str or "No response from LLM"}


if __name__ == '__main__':
    print("Testing LLM Handler...")
    # This requires OPENAI_API_KEY to be set in the environment.
    if not os.getenv("OPENAI_API_KEY"):
        print("SKIPPING LLM HANDLER TEST: OPENAI_API_KEY environment variable not set.")
    else:
        print("OPENAI_API_KEY found. Proceeding with tests.")
        # Test 1: Determine Applicable BREFs
        print("\n--- Test 1: Determine Applicable BREFs ---")
        sample_permit_activities = "The facility is involved in the intensive rearing of poultry, specifically chickens for meat production, with a capacity of 50,000 birds. It also includes a small-scale feed mill on site."
        sample_bref_scopes = [
            {"bref_id": "BREF_POULTRY_PIGS", "scope_description": "This BREF concerns the intensive rearing of poultry (more than 40,000 places for poultry) and/or pigs (more than 2,000 places for production pigs or 750 places for sows)."},
            {"bref_id": "BREF_CEMENT_LIME", "scope_description": "This BREF concerns the production of cement clinker in rotary kilns and the production of lime in kilns."},
            {"bref_id": "BREF_FOOD_DRINK_MILK", "scope_description": "This BREF concerns the treatment and processing of milk, the quantity of milk received being greater than 200 tonnes per day (average value on an annual basis)."}
        ]
        applicable_brefs_result = determine_applicable_brefs(sample_permit_activities, sample_bref_scopes)
        print("\nApplicable BREFs Result (JSON):")
        print(json.dumps(applicable_brefs_result, indent=2))

        # Test 2: Verify Permit Compliance with BAT
        print("\n--- Test 2: Verify Permit Compliance with BAT ---")
        sample_permit_text_md = """
        # Permit for Facility Alpha
        ## Section 3: Emission Limits
        3.1. Dust emissions from the main stack shall not exceed 10 mg/Nm3.
        3.2. Ammonia (NH3) emissions from poultry housing unit A shall be managed using best available techniques to minimize environmental impact. Regular monitoring of internal housing conditions is required.
        ## Section 4: Monitoring
        4.1. Ammonia levels in housing unit A shall be recorded weekly.
        """
        sample_bat_conclusion = {
            "bat_id": "BAT_POULTRY_NH3_12",
            "bat_text_description": "BAT 12. In order to reduce ammonia emissions to air from the housing of chickens for meat production (broilers), BAT is to use one or a combination of the techniques given below. Techniques include nutritional strategies, specific housing designs, and air cleaning systems.",
            "source_metadata": {"page_number": "150", "paragraph_id": "BAT12.A"}
        }
        compliance_result = verify_permit_compliance_with_bat(sample_permit_text_md, sample_bat_conclusion)
        print("\nCompliance Verification Result (JSON):")
        print(json.dumps(compliance_result, indent=2))

        # Test with a BAT that is likely not covered
        print("\n--- Test 3: Verify Permit Compliance with an unrelated BAT ---")
        sample_bat_unrelated = {
            "bat_id": "BAT_CEMENT_DUST_5",
            "bat_text_description": "BAT 5. In order to prevent or reduce diffuse dust emissions from conveying, loading, unloading, and storage of raw materials and fuels in cement plants, BAT is to use enclosed systems and/or apply abatement techniques such as fabric filters.",
            "source_metadata": {"page_number": "80", "paragraph_id": "BAT5.C"}
        }
        compliance_result_unrelated = verify_permit_compliance_with_bat(sample_permit_text_md, sample_bat_unrelated)
        print("\nCompliance Verification Result for Unrelated BAT (JSON):")
        print(json.dumps(compliance_result_unrelated, indent=2))

