"""
Clarification tool for asking users to refine their questions.

This tool helps the agent ask follow-up questions when:
- The initial query is too vague or ambiguous
- The database search returned no results
- The user's intent is unclear
- More context would improve search results

Location-aware clarifications for:
- Woonasquatucket River Watershed Council (Providence, RI)
- Rhode Island community resources
"""

import logging
from typing import Optional
from langchain_core.tools import tool

log = logging.getLogger('vecinita_pipeline.agent.tools.clarify')

# Location context for clarifications
LOCATION_CONTEXT = {
    "organization": "Woonasquatucket River Watershed Council",
    "location": "Providence, Rhode Island",
    "region": "Rhode Island"
}


@tool
def clarify_question(
    original_question: str,
    search_context: Optional[str] = None,
    reason_for_clarification: str = "Your question is too broad"
) -> str:
    """
    Ask the user clarifying questions to refine their search.

    This tool is used when:
    - The initial search returned no results
    - The question is ambiguous or very broad
    - More context would improve the response

    Args:
        original_question: The user's original question
        search_context: What we searched for and didn't find (optional)
        reason_for_clarification: Why we're asking for clarification

    Returns:
        A natural language response asking clarifying questions
    """
    log.info(f"Clarify Question: Original question: '{original_question}'")
    log.info(f"Clarify Question: Reason: {reason_for_clarification}")

    # Generate contextual clarifying questions based on the original question
    # Now includes location-aware clarifications for Rhode Island
    clarification_prompts = {
        "location": [
            f"Are you asking about resources in {LOCATION_CONTEXT['location']} specifically?",
            "Which city or town in Rhode Island are you interested in?",
            f"Is this related to the {LOCATION_CONTEXT['region']} area or elsewhere?",
            "Are you looking for programs in a specific neighborhood or district?"
        ],
        "doctor": [
            "What type of doctor or healthcare provider are you looking for? (e.g., general practitioner, specialist)",
            "Are you looking for someone who accepts your insurance?",
            "Do you need urgent care or a regular appointment?",
            f"Are you looking for providers in {LOCATION_CONTEXT['location']}?"
        ],
        "service": [
            "What specific service or program are you interested in?",
            "Can you give me more details about what you're looking for?",
            "Are you looking for environmental, educational, or community health services?",
            f"Is this related to {', '.join(['watershed protection', 'community health', 'environmental education'])}?"
        ],
        "watershed": [
            f"Are you asking about the Woonasquatucket River Watershed specifically?",
            "Are you interested in habitat restoration, water quality, or community education?",
            "What aspect of watershed management interests you?",
            f"Are you a community member, volunteer, or researcher?"
        ],
        "general": [
            f"Could you provide more context? Are you asking about something in {LOCATION_CONTEXT['location']}?",
            "What is the specific problem or topic you need help with?",
            "Are there any particular aspects you'd like me to focus on?",
            f"Is this related to community resources, environmental, or health services in {LOCATION_CONTEXT['region']}?"
        ]
    }

    # Detect question type to provide relevant clarifications
    question_lower = original_question.lower()

    if any(word in question_lower for word in ["watershed", "river", "water quality", "habitat", "environment", "wetland"]):
        category = "watershed"
    elif any(word in question_lower for word in ["doctor", "medical", "health", "hospital", "clinic", "provider"]):
        category = "doctor"
    elif any(word in question_lower for word in ["near", "location", "where", "place", "address", "area"]):
        category = "location"
    elif any(word in question_lower for word in ["what", "how", "service", "program", "resource"]):
        category = "service"
    else:
        category = "general"

    prompts = clarification_prompts.get(
        category, clarification_prompts["general"])

    response = (
        f"I need a bit more information to help you better.\n\n"
        f"**Your question:** \"{original_question}\"\n\n"
        f"**Why:** {reason_for_clarification}.\n\n"
        f"**Could you clarify:**\n"
    )

    for i, prompt in enumerate(prompts[:3], 1):
        response += f"{i}. {prompt}\n"

    response += f"\nOnce you provide more details, I can give you a more accurate answer from our {LOCATION_CONTEXT['location']} community resources."

    log.info(f"Clarify Question: Generated location-aware clarification response")
    return response


def create_clarify_question_tool():
    """Create an instance of the clarify_question tool."""
    return clarify_question
