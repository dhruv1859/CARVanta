def generate_decision(cvs: float, confidence: float) -> dict:

    # Decision logic
    if cvs >= 0.93:
        decision = "Recommended"
    elif cvs >= 0.85:
        decision = "Consider"
    elif cvs >= 0.70:
        decision = "Experimental"
    else:
        decision = "Avoid"

    # Confidence label
    if confidence >= 0.9:
        confidence_label = "High"
    elif confidence >= 0.8:
        confidence_label = "Medium"
    else:
        confidence_label = "Low"

    return {
        "decision": decision,
        "confidence_label": confidence_label
    }
    
def recommend_antigen(results: list) -> dict:

    if not results:
        return {"recommendation": "No data available"}

    best = results[0]

    return {
        "best_antigen": best["antigen"],
        "reason": f"{best['antigen']} shows highest CAR viability score with strong confidence."
    }