import gradio as gr
from generator import stream_enterprise_brochure

def generate_brochure_ui(company_name, target_url, engine_choice):
    if not company_name.strip() or not target_url.strip():
        yield "⚠️ Please provide both a Company Name and a valid Website URL."
        return
    
    yield from stream_enterprise_brochure(company_name.strip(), target_url.strip(), engine_choice)

def create_ui():
    with gr.Blocks(title="Enterprise Company Dossier & Brochure Generator") as demo:
        gr.Markdown("# 🏢 Automated Enterprise Brochure & Research Generator")
        gr.Markdown(
            "An autonomous research pipeline that crawls corporate websites, filters relevant architecture "
            "(About, Careers, Tech), and synthesizes publication-grade executive brochures via LLM streaming."
        )

        with gr.Row():
            with gr.Column(scale=1):
                company_name_input = gr.Textbox(
                    label="Company Name",
                    placeholder="e.g. Hugging Face, DeepSeek, Stripe",
                    lines=1
                )
                url_input = gr.Textbox(
                    label="Primary Website URL",
                    placeholder="https://example.com",
                    lines=1
                )
                engine_selector = gr.Dropdown(
                    choices=["Gemini (Cloud)", "Ollama (Llama 3.2 Local)"],
                    value="Gemini (Cloud)",
                    label="LLM Synthesis Engine",
                    interactive=True
                )
                generate_btn = gr.Button("Generate Enterprise Brochure", variant="primary")
                
                gr.Examples(
                    examples=[
                        ["Hugging Face", "https://huggingface.co", "Gemini (Cloud)"],
                        ["DeepSeek", "https://www.deepseek.com", "Gemini (Cloud)"]
                    ],
                    inputs=[company_name_input, url_input, engine_selector]
                )
            
            with gr.Column(scale=2):
                output_markdown = gr.Markdown(
                    label="Generated Corporate Brochure",
                    value="*Brochure output will stream here in real time...*"
                )

        generate_btn.click(
            generate_brochure_ui,
            inputs=[company_name_input, url_input, engine_selector],
            outputs=[output_markdown]
        )
        url_input.submit(
            generate_brochure_ui,
            inputs=[company_name_input, url_input, engine_selector],
            outputs=[output_markdown]
        )

    return demo

if __name__ == "__main__":
    demo = create_ui()
    # Runs on localhost with built-in optional authentication if needed
    demo.launch(server_name="127.0.0.1", server_port=7861)
