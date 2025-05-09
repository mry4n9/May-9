# utils/prompt_builder.py

def get_combined_context(url_summary, additional_summary, downloadable_summary):
    context_parts = []
    if url_summary and "Error" not in url_summary:
        context_parts.append(f"Website Context Summary:\n{url_summary}")
    if additional_summary and "Error" not in additional_summary:
        context_parts.append(f"Additional Company Context Summary:\n{additional_summary}")
    if downloadable_summary and "Error" not in downloadable_summary:
        context_parts.append(f"Downloadable Material (e.g., White Paper) Summary:\n{downloadable_summary}")
    
    if not context_parts:
        return "No context provided or extracted."
    return "\n\n---\n\n".join(context_parts)

def create_email_prompt(full_context, lead_objective_type, links, version_number):
    # lead_objective_type is "Demo Booking" or "Sales Meeting"
    # links is a dict: {'learn_more': str, 'downloadable': str, 'objective_link': str}
    
    # Determine which link to emphasize based on lead_objective_type
    primary_link = links.get('objective_link', '#error-link-missing')
    if lead_objective_type == "Sales Meeting":
        objective_action = "book a sales meeting"
    else: # Default to Demo Booking
        objective_action = "book a demo"

    link_to_embed = f"[{objective_action.title()}]({primary_link})"
    if links.get('downloadable'):
        link_to_embed += f" or [Download Our Material]({links.get('downloadable')})"


    return f"""
    Company & Material Context:
    ---
    {full_context}
    ---

    Task: Generate content for one version of a progressive weekly email.
    Overall Campaign Lead Objective: {lead_objective_type} (aiming to get recipients to {objective_action}).
    Email Specific Objective: Demand Capture.

    Email Content Requirements:
    1.  **Headline**: Engaging headline for the email preview (not the subject line).
    2.  **Subject Line**: Compelling subject line to maximize open rates.
    3.  **Body**: 2-3 paragraphs. The tone should be professional yet persuasive. 
        It should build interest progressively.
        Embed a call to action link: {link_to_embed}.
        The body should naturally lead to this call to action.
    4.  **CTA**: A condensed version of the call to action in the body (e.g., "Book Your Demo Now", "Schedule a Meeting").

    This is version #{version_number} of the email sequence.

    Output the response as a single JSON object with keys: "headline", "subject_line", "body", "cta".
    Example JSON:
    {{
      "headline": "Unlock Growth This Quarter",
      "subject_line": "Your Path to [Benefit] Starts Here",
      "body": "Paragraph 1 introducing a challenge or opportunity related to the company's offerings based on the context provided...\n\nParagraph 2 detailing how the company's solution addresses this, referencing specifics from the context...\n\nReady to see how we can help you {objective_action}? {link_to_embed}.",
      "cta": "Explore {objective_action.title()}"
    }}
    """

def create_linkedin_facebook_prompt(platform, full_context, lead_objective_type, links, ad_objective, version_number):
    # platform: "LinkedIn" or "FaceBook"
    # ad_objective: "Brand Awareness", "Demand Gen", "Demand Capture"
    
    intro_char_limit = "300-400 characters (hook in first 150)" if platform == "LinkedIn" else "300-400 characters (hook in first 125)"
    headline_char_limit = "~70 characters" if platform == "LinkedIn" else "~27 characters"
    
    destination_info = ""
    if ad_objective == "Brand Awareness":
        destination_info = f"The ad should encourage users to learn more, potentially linking to: {links.get('learn_more', '#')}"
    elif ad_objective == "Demand Gen":
        destination_info = f"The ad should encourage users to download material, linking to: {links.get('downloadable', '#')}"
    elif ad_objective == "Demand Capture":
        destination_info = f"The ad should encourage users to book a demo/meeting, linking to: {links.get('objective_link', '#')}"

    json_keys = ["ad_name", "introductory_text" if platform == "LinkedIn" else "primary_text", "image_copy", "headline"]
    example_json = {
        "ad_name": f"{platform} Ad - ContextBased - {ad_objective} - V{version_number}",
        "introductory_text" if platform == "LinkedIn" else "primary_text": f"Hook... Engaging text with emojis 😊. Max {intro_char_limit.split('(')[0].strip()}.",
        "image_copy": "Text for the ad's image/visual.",
        "headline": f"Catchy Headline ({headline_char_limit})"
    }
    if platform == "FaceBook":
        json_keys.append("link_description")
        example_json["link_description"] = "Short Link Desc. (~27 chars)"

    return f"""
    Company & Material Context:
    ---
    {full_context}
    ---

    Task: Generate ad copy for one version of a {platform} ad.
    Overall Campaign Lead Objective: {lead_objective_type}.
    Specific Ad Objective for this version: {ad_objective}.
    {destination_info}

    Ad Copy Requirements for {platform} (Version #{version_number}):
    1.  **Ad Name**: A unique identifier for this ad, up to 250 characters.
    2.  **{'Introductory Text' if platform == "LinkedIn" else 'Primary Text'}**: {intro_char_limit}. Must include relevant emojis.
    3.  **Image Copy**: Text to be used on or inspire the ad's image/visual.
    4.  **Headline**: {headline_char_limit}.
    {'''5.  **Link Description**: ~27 characters (for Facebook only).''' if platform == "FaceBook" else ""}

    Tailor the messaging to the '{ad_objective}' objective.
    - Brand Awareness: Focus on introducing the company/product and its value.
    - Demand Gen: Focus on the value of the downloadable material and encourage downloads.
    - Demand Capture: Focus on the benefits of a demo/meeting and encourage sign-ups.

    Output the response as a single JSON object with keys: {json_keys}.
    Example JSON:
    {json.dumps(example_json, indent=2)}
    """

def create_google_search_prompt(full_context, lead_objective_type, links):
    return f"""
    Company & Material Context:
    ---
    {full_context}
    ---

    Task: Generate Google Search Ad copy.
    Overall Campaign Lead Objective: {lead_objective_type}.
    Links available: Learn More ({links.get('learn_more')}), Downloadable ({links.get('downloadable')}), Objective ({links.get('objective_link')}).

    Requirements:
    -   **Headlines**: Create exactly 15 headlines. Each headline should be ~30 characters.
    -   **Descriptions**: Create exactly 4 descriptions. Each description should be ~90 characters.

    The copy should be concise, compelling, and include strong calls to action where appropriate.
    Focus on keywords and benefits relevant to the provided context and lead objective.

    Output the response as a single JSON object with two keys: "headlines" (a list of 15 strings) and "descriptions" (a list of 4 strings).
    Example JSON:
    {{
      "headlines": ["Headline 1 (Max 30)", "Headline 2 (Max 30)", ..., "Headline 15 (Max 30)"],
      "descriptions": ["Description 1 (Max 90 chars). CTA.", "Description 2 (Max 90 chars). Benefit.", ..., "Description 4 (Max 90 chars)."]
    }}
    """

def create_google_display_prompt(full_context, lead_objective_type, links):
    return f"""
    Company & Material Context:
    ---
    {full_context}
    ---

    Task: Generate Google Display Ad copy.
    Overall Campaign Lead Objective: {lead_objective_type}.
    Links available: Learn More ({links.get('learn_more')}), Downloadable ({links.get('downloadable')}), Objective ({links.get('objective_link')}).

    Requirements:
    -   **Headlines**: Create exactly 5 short headlines. Each headline should be ~30 characters.
    -   **Descriptions**: Create exactly 5 long headlines/descriptions. Each should be ~90 characters.

    The copy should be engaging and suitable for display ad formats.
    Focus on visual appeal and clear messaging.

    Output the response as a single JSON object with two keys: "headlines" (a list of 5 strings) and "descriptions" (a list of 5 strings).
    Example JSON:
    {{
      "headlines": ["Short Headline 1", "Short Headline 2", ..., "Short Headline 5"],
      "descriptions": ["Longer Description 1 (90 chars)", "Longer Description 2 (90 chars)", ..., "Longer Description 5 (90 chars)"]
    }}
    """

def create_reasoning_prompt(url_summary, additional_summary, downloadable_summary, generated_ad_counts):
    full_context = get_combined_context(url_summary, additional_summary, downloadable_summary)
    
    return f"""
    You were provided with the following summarized contexts:
    ---
    {full_context}
    ---

    Based on these contexts and specific objectives, you (conceptually) generated the following quantities of ad copy:
    - Emails: {generated_ad_counts.get('email', 0)}
    - LinkedIn Ads (Brand Awareness): {generated_ad_counts.get('linkedin_awareness', 0)}
    - LinkedIn Ads (Demand Gen): {generated_ad_counts.get('linkedin_demand_gen', 0)}
    - LinkedIn Ads (Demand Capture): {generated_ad_counts.get('linkedin_demand_capture', 0)}
    - Facebook Ads (Brand Awareness): {generated_ad_counts.get('facebook_awareness', 0)}
    - Facebook Ads (Demand Gen): {generated_ad_counts.get('facebook_demand_gen', 0)}
    - Facebook Ads (Demand Capture): {generated_ad_counts.get('facebook_demand_capture', 0)}
    - Google Search Ads: 1 set (15 headlines, 4 descriptions)
    - Google Display Ads: 1 set (5 headlines, 5 descriptions)

    Task: Provide a brief explanation of your thought process for generating this ad content. 
    Describe how you (would have) utilized the provided contexts to tailor the ad copy. 
    For example:
    - What key themes, pain points, solutions, or calls to action did you identify from the context?
    - How did you weave them into the different ad formats (Email, LinkedIn, Facebook, Google Search/Display)?
    - How did you differentiate messaging for various objectives (Brand Awareness, Demand Gen, Demand Capture)?
    - Be specific about how different parts of the context might have influenced different types of ads or messages.
    
    This explanation is for transparency, to help the user understand the connection between their input materials and the generated ads.
    Keep the explanation concise yet informative, around 3-5 paragraphs.
    Do not output JSON. Output plain text.
    """