import gradio as gr
import httpx

API_BASE = "http://localhost:8000"


def ask_question(question: str, mode: str, top_k: int) -> tuple:
    if not question.strip():
        return "Please enter a question.", ""

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{API_BASE}/api/v1/ask",
                params={"query": question, "mode": mode, "top_k": int(top_k)},
            )
        data = response.json()

        answer = data.get("answer", "No answer returned.")
        sources = data.get("sources", [])
        from_cache = data.get("from_cache", False)

        sources_text = ""
        if sources:
            sources_text = "**Sources:**\n"
            for s in sources:
                authors = ", ".join(s.get("authors", [])[:2])
                sources_text += f"- [{s['arxiv_id']}] {s['title']} — {authors}\n"

        if from_cache:
            answer = "(cached)\n\n" + answer

        return answer, sources_text

    except Exception as e:
        return f"Error: {e}", ""


with gr.Blocks(title="arXiv Paper Curator") as demo:
    gr.Markdown(
        "# 📄 arXiv Paper Curator\nAsk questions about the latest AI/ML research papers."
    )

    with gr.Row():
        with gr.Column(scale=3):
            question = gr.Textbox(
                label="Your Question",
                placeholder="e.g. What are the latest advances in RAG systems?",
                lines=3,
            )
        with gr.Column(scale=1):
            mode = gr.Radio(
                choices=["hybrid", "semantic", "keyword"],
                value="hybrid",
                label="Search Mode",
            )
            top_k = gr.Slider(
                minimum=1,
                maximum=10,
                value=5,
                step=1,
                label="Number of chunks",
            )

    submit_btn = gr.Button("Ask", variant="primary")

    with gr.Row():
        with gr.Column(scale=2):
            answer = gr.Markdown(label="Answer")
        with gr.Column(scale=1):
            sources = gr.Markdown(label="Sources")

    submit_btn.click(
        fn=ask_question, inputs=[question, mode, top_k], outputs=[answer, sources]
    )
    question.submit(
        fn=ask_question, inputs=[question, mode, top_k], outputs=[answer, sources]
    )


if __name__ == "__main__":
    demo.launch(
        server_port=7861,
        server_name="127.0.0.1",
        share=False,
    )
