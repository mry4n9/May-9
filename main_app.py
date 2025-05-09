# main_app.py
import streamlit as st
from urllib.parse import urlparse
import time
import json

from utils.text_extractor import extract_text_from_url, extract_text_from_file
from utils.ai_helper import summarize_text_with_ai, generate_content_with_ai
from utils.prompt_builder import (
    get_combined_context, create_email_prompt,
    create_linkedin_facebook_prompt, create_google_search_prompt,
    create_google_display_prompt, create_reasoning_prompt
)
from utils.excel_writer import create_excel_report

st.set_page_config(page_title="Branding & Marketing AI Tool", layout="wide")

# --- Helper Functions ---
def get_company_name_from_url(url):
    if not url:
        return "brand"
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        parsed_url = urlparse(url)
        domain_parts = parsed_url.netloc.split('.')
        if len(domain_parts) > 2 and domain_parts[-2] not in ['co', 'com', 'org', 'net', 'gov', 'edu']:
            return domain_parts[-2]
        elif len(domain_parts) > 1:
             return domain_parts[-2] if len(domain_parts) > 2 else domain_parts[0]
        return domain_parts[0] if domain_parts else "brand"
    except Exception:
        return "brand"

# --- UI ---
st.title("🚀 AI-Powered Branding & Marketing Content Generator")
st.markdown("Extract insights from your materials and generate tailored ad copy.")

# --- Session State Initialization ---
if 'generation_complete' not in st.session_state:
    st.session_state.generation_complete = False
if 'excel_bytes' not in st.session_state:
    st.session_state.excel_bytes = None
if 'excel_filename' not in st.session_state:
    st.session_state.excel_filename = ""
if 'error_messages' not in st.session_state:
    st.session_state.error_messages = []


# --- Inputs ---
st.sidebar.header("⚙️ Configuration")

st.sidebar.subheader("1. Company Context")
client_url = st.sidebar.text_input("Client's Website URL (e.g., example.com)", "")
additional_context_file = st.sidebar.file_uploader("Upload Additional Context (PDF/PPTX)", type=['pdf', 'pptx'])
downloadable_material_file = st.sidebar.file_uploader("Upload Downloadable Lead Material (PDF/PPTX)", type=['pdf', 'pptx'])

st.sidebar.subheader("2. Campaign Details")
lead_objective_options = ["Demo Booking", "Sales Meeting"]
lead_objective_choice = st.sidebar.selectbox("Primary Lead Objective", lead_objective_options)

content_count = st.sidebar.slider("Content Versions per Objective (Email, LinkedIn, Facebook)", 1, 20, 1)

st.sidebar.subheader("3. Links for Ads")
learn_more_link = st.sidebar.text_input("Link for 'Learn More' (Brand Awareness)", "https://example.com/learn-more")
downloadable_material_link = st.sidebar.text_input("Link to Downloadable Material (Demand Gen)", "https://example.com/whitepaper-download")
objective_link_default = "https://example.com/book-demo" if lead_objective_choice == "Demo Booking" else "https://example.com/contact-sales"
objective_link = st.sidebar.text_input(f"Link for '{lead_objective_choice}' (Demand Capture)", objective_link_default)

links_for_ads = {
    'learn_more': learn_more_link,
    'downloadable': downloadable_material_link,
    'objective_link': objective_link
}

# --- Main Area ---
col1, col2 = st.columns([0.7, 0.3])

with col1:
    st.header("Generated Ad Content Preview")
    if st.session_state.generation_complete and st.session_state.excel_bytes:
        st.success(f"Excel report '{st.session_state.excel_filename}' generated successfully!")
        st.download_button(
            label=f"📥 Download {st.session_state.excel_filename}",
            data=st.session_state.excel_bytes,
            file_name=st.session_state.excel_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.info("The Excel file contains multiple sheets: Email, LinkedIn, FaceBook, Google Search, Google Display, and Reasoning.")
    elif st.session_state.error_messages:
        unique_errors = list(dict.fromkeys(st.session_state.error_messages))
        for error in unique_errors:
            st.error(error)
    else:
        st.info("Configure inputs in the sidebar and click 'Generate Content' to begin.")

with col2:
    st.image("https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.png", width=200)
    if st.sidebar.button("✨ Generate Content", type="primary", use_container_width=True):
        st.session_state.generation_complete = False
        st.session_state.excel_bytes = None
        st.session_state.excel_filename = ""
        st.session_state.error_messages = []

        if not client_url:
            st.sidebar.error("Client's Website URL is required.")
            st.stop()

        api_key = st.secrets.get("OPENAI_API_KEY")
        if not api_key:
            st.sidebar.error("OpenAI API key not found in secrets.toml.")
            st.stop()

        progress_bar = st.sidebar.progress(0)
        status_text = st.sidebar.empty()

        total_steps = 5
        total_steps += content_count
        total_steps += 3 * content_count
        total_steps += 3 * content_count
        total_steps += 2
        total_steps += 1
        total_steps += 1
        
        current_step = 0 

        def update_progress(message):
            global current_step
            current_step += 1
            progress_value = min(1.0, current_step / total_steps if total_steps > 0 else 0)
            progress_bar.progress(progress_value)
            status_text.info(f"⏳ {message}")

        all_ad_data = {
            'email': [], 'linkedin': [], 'facebook': [],
            'google_search': {}, 'google_display': {},
            'reasoning': {}
        }
        summaries = {'url': None, 'additional': None, 'downloadable': None}

        try:
            # 1. Extract and Summarize Context
            update_progress("Extracting website content...")
            url_text = extract_text_from_url(client_url)
            if "Error" in (url_text or ""):
                st.session_state.error_messages.append(f"URL Text Extraction: {url_text}")
            else:
                update_progress("Summarizing website content...")
                summaries['url'] = summarize_text_with_ai(url_text)
                if "Error" in (summaries['url'] or ""): st.session_state.error_messages.append(f"URL Summary: {summaries['url']}")


            if additional_context_file:
                update_progress("Extracting additional context...")
                additional_text = extract_text_from_file(additional_context_file)
                if "Error" in (additional_text or ""):
                     st.session_state.error_messages.append(f"Additional Context Extraction: {additional_text}")
                else:
                    update_progress("Summarizing additional context...")
                    summaries['additional'] = summarize_text_with_ai(additional_text)
                    if "Error" in (summaries['additional'] or ""): st.session_state.error_messages.append(f"Additional Context Summary: {summaries['additional']}")


            if downloadable_material_file:
                update_progress("Extracting downloadable material...")
                downloadable_text = extract_text_from_file(downloadable_material_file)
                if "Error" in (downloadable_text or ""):
                    st.session_state.error_messages.append(f"Downloadable Material Extraction: {downloadable_text}")
                else:
                    update_progress("Summarizing downloadable material...")
                    summaries['downloadable'] = summarize_text_with_ai(downloadable_text)
                    if "Error" in (summaries['downloadable'] or ""): st.session_state.error_messages.append(f"Downloadable Material Summary: {summaries['downloadable']}")

            full_context_for_prompts = get_combined_context(summaries['url'], summaries['additional'], summaries['downloadable'])
            if "No context" in full_context_for_prompts and not (summaries['url'] or summaries['additional'] or summaries['downloadable']):
                 st.session_state.error_messages.append("No usable context was extracted or summarized. Cannot generate ads effectively.")

            # 2. Generate Ad Content
            # Emails
            for i in range(content_count):
                update_progress(f"Generating Email content (Version {i+1}/{content_count})...")
                prompt = create_email_prompt(full_context_for_prompts, lead_objective_choice, links_for_ads, i + 1)
                response = generate_content_with_ai(prompt)
                if isinstance(response, dict) and "error" not in response:
                    all_ad_data['email'].append(response)
                else: st.session_state.error_messages.append(f"Email Gen Error V{i+1}: {response.get('error', response) if isinstance(response, dict) else response}")


            # LinkedIn & Facebook
            social_platforms = {
                "LinkedIn": {"objectives": ["Brand Awareness", "Demand Gen", "Demand Capture"], "key": "linkedin"},
                "FaceBook": {"objectives": ["Brand Awareness", "Demand Gen", "Demand Capture"], "key": "facebook"}
            }
            cta_map = {
                "LinkedIn": {"Brand Awareness": "Learn More", "Demand Gen": "Download", "Demand Capture": "Request Demo"},
                "FaceBook": {"Brand Awareness": "Learn More", "Demand Gen": "Download", "Demand Capture": "Book Now"}
            }

            for platform_name, config in social_platforms.items():
                for ad_obj in config["objectives"]:
                    for i in range(content_count):
                        update_progress(f"Generating {platform_name} {ad_obj} (V{i+1}/{content_count})...")
                        prompt = create_linkedin_facebook_prompt(platform_name, full_context_for_prompts, lead_objective_choice, links_for_ads, ad_obj, i + 1)
                        response = generate_content_with_ai(prompt)
                        if isinstance(response, dict) and "error" not in response:
                            if ad_obj == "Brand Awareness":
                                response["destination_url"] = links_for_ads.get('learn_more', '#')
                                response["cta_button"] = cta_map[platform_name][ad_obj]
                            elif ad_obj == "Demand Gen":
                                response["destination_url"] = links_for_ads.get('downloadable', '#')
                                response["cta_button"] = cta_map[platform_name][ad_obj]
                            elif ad_obj == "Demand Capture":
                                response["destination_url"] = links_for_ads.get('objective_link', '#')
                                response["cta_button"] = cta_map[platform_name][ad_obj]
                            response["objective_type"] = ad_obj
                            all_ad_data[config["key"]].append(response)
                        else: st.session_state.error_messages.append(f"{platform_name} {ad_obj} V{i+1} Error: {response.get('error', response) if isinstance(response, dict) else response}")


            # Google Search
            update_progress("Generating Google Search ads...")
            prompt = create_google_search_prompt(full_context_for_prompts, lead_objective_choice, links_for_ads)
            response = generate_content_with_ai(prompt)
            if isinstance(response, dict) and "error" not in response:
                all_ad_data['google_search'] = response
            else: st.session_state.error_messages.append(f"Google Search Ads Error: {response.get('error', response) if isinstance(response, dict) else response}")


            # Google Display
            update_progress("Generating Google Display ads...")
            prompt = create_google_display_prompt(full_context_for_prompts, lead_objective_choice, links_for_ads)
            response = generate_content_with_ai(prompt)
            if isinstance(response, dict) and "error" not in response:
                all_ad_data['google_display'] = response
            else: st.session_state.error_messages.append(f"Google Display Ads Error: {response.get('error', response) if isinstance(response, dict) else response}")


            # Reasoning Page Content
            update_progress("Generating AI reasoning explanation...")
            generated_counts = {
                'email': len(all_ad_data['email']),
                'linkedin_awareness': sum(1 for ad in all_ad_data['linkedin'] if ad.get("objective_type") == "Brand Awareness"),
                'linkedin_demand_gen': sum(1 for ad in all_ad_data['linkedin'] if ad.get("objective_type") == "Demand Gen"),
                'linkedin_demand_capture': sum(1 for ad in all_ad_data['linkedin'] if ad.get("objective_type") == "Demand Capture"),
                'facebook_awareness': sum(1 for ad in all_ad_data['facebook'] if ad.get("objective_type") == "Brand Awareness"),
                'facebook_demand_gen': sum(1 for ad in all_ad_data['facebook'] if ad.get("objective_type") == "Demand Gen"),
                'facebook_demand_capture': sum(1 for ad in all_ad_data['facebook'] if ad.get("objective_type") == "Demand Capture"),
            }
            prompt = create_reasoning_prompt(summaries['url'], summaries['additional'], summaries['downloadable'], generated_counts)
            ai_reasoning_text = generate_content_with_ai(prompt, expect_json=False)

            all_ad_data['reasoning'] = {
                'url_summary': summaries['url'] or "Not provided/extracted.",
                'additional_summary': summaries['additional'] or "Not provided/extracted.",
                'downloadable_summary': summaries['downloadable'] or "Not provided/extracted.",
                'ai_reasoning': ai_reasoning_text if not (isinstance(ai_reasoning_text, str) and "Error" in ai_reasoning_text) else "Could not generate AI reasoning."
            }
            if isinstance(ai_reasoning_text, str) and "Error" in ai_reasoning_text: st.session_state.error_messages.append(f"AI Reasoning Error: {ai_reasoning_text}")


            # 3. Create Excel Report
            has_data = any(all_ad_data[key] for key in ['email', 'linkedin', 'facebook', 'google_search', 'google_display'])

            if has_data:
                update_progress("Creating Excel report...")
                company_name_for_file = get_company_name_from_url(client_url)
                excel_bytes, excel_filename = create_excel_report(all_ad_data, company_name_for_file, lead_objective_choice)

                st.session_state.excel_bytes = excel_bytes
                st.session_state.excel_filename = excel_filename
                st.session_state.generation_complete = True
                if not st.session_state.error_messages:
                    status_text.success("✅ Content generation complete! Download your report.")
                else:
                    status_text.warning("⚠️ Content generation partially complete with some errors. Report available.")
            else:
                status_text.error("❌ Generation failed. No content to create Excel report. Check errors above.")
                st.session_state.generation_complete = False


        except ValueError as ve:
            status_text.error(f"❌ Critical Error: {ve}")
            st.session_state.error_messages.append(str(ve))
            st.session_state.generation_complete = False
        except Exception as e:
            status_text.error(f"❌ An unexpected error occurred: {e}")
            st.session_state.error_messages.append(f"Unexpected Error: {str(e)}")
            st.session_state.generation_complete = False
            # import traceback
            # st.error(traceback.format_exc())
        finally:
            progress_bar.progress(1.0)
            # Rerun to update the UI based on session state changes
            st.rerun() # CORRECTED: Use st.rerun()