import re

def validate(llm_output: str):
    """
    Validate if ground truth 'PA' or 'Pennsylvania' and its number (rounded to 2 decimals) 
    are present in LLM output.
    
    Returns:
        (True, "OK") if found
        (False, reason) if not
    """
    ground_truth_value = 3.699395770392749
    gt_rounded = round(ground_truth_value, 2)

    has_pennsylvania = re.search(r"\bPennsylvania\b", llm_output, re.IGNORECASE)
    has_pa_token = re.search(r"(?<![A-Za-z])PA(?![a-z])", llm_output)
    if not has_pennsylvania and not has_pa_token:
        return False, "Missing name: ['PA', 'Pennsylvania']"

    for m in re.findall(r"\d+\.\d+", llm_output):
        try:
            val = float(m)
            if round(val, 2) == gt_rounded:
                return True, f"Found: value≈{gt_rounded}"
        except ValueError:
            continue

    return False, f"No matching number (≈{gt_rounded}) found in LLM output."


