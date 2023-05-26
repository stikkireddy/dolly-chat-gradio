# Databricks notebook source
# MAGIC %pip install Jinja2==3.0.3 fastapi uvicorn nest_asyncio gradio==3.19.1

# COMMAND ----------

from databricks_magic import DatabricksApp
dbx_app = DatabricksApp(8098)

# COMMAND ----------

import gradio as gr


# Add text data to history to quickly render text
def add_text(history, text):
    history = history + [(text, None)]
    return history, ""


# Make api call to dolly
def dolly_request(message, temperature=0.5, max_tokens=100,
                  endpoint=None,
                  token=None):
    import requests
    resp = requests.post(endpoint, json={
        "dataframe_split": {
            "columns": [
                "message",
                "temperature",
                "max_tokens"
            ],
            "data": [
                [
                    message,
                    temperature,
                    max_tokens
                ]
            ]
        }
    }, headers={"Authorization": f"Bearer {token}"})
    return resp.json()["predictions"]


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


def bot(history, temperature, max_tokens, endpoint, token):
    # time.sleep(20)
    msg = history[-1][0]
    print(f"Logging message: {msg}, temp: {temperature}, max_tokens: {max_tokens}, endpoint: {endpoint}")
    try:
        prediction = dolly_request(msg, temperature, max_tokens, endpoint, token)
        prediction = remove_prefix(prediction, msg)
    except KeyError:
        prediction = "Error: Invalid endpoint or token."
    history[-1][1] = prediction
    return history


def clear_history(history):
    return []


with gr.Blocks() as demo:
    gr.Markdown("# Dolly Chatbot Powered By Databricks ML Serving")
    with gr.Accordion("Settings", open=True):
        with gr.Row():
            endpoint = gr.Textbox(label="Endpoint Url", interactive=True)
            token = gr.Textbox(label="Token", interactive=True, type="password")

        with gr.Row():
            temp_slider = gr.Slider(0, 1, step=0.01, value=0.5,
                                    label="Temperature", info="Choose between 0 and 1", interactive=True)
            max_tokens_slider = gr.Slider(100, 1000, step=10, value=100,
                                          label="Max Tokens", info="Choose between 100 and 1000", interactive=True)

    chatbot = gr.Chatbot([], elem_id="chatbot").style(height=500)
    with gr.Row():
        with gr.Column(scale=0.85):
            txt = gr.Textbox(
                show_label=False,
                placeholder="Enter text and press enter.",
            ).style(container=False)
        with gr.Column(scale=0.15, min_width=0):
            btn = gr.Button("Clear")

    txt.submit(add_text, [chatbot, txt], [chatbot, txt]).then(
        bot, [chatbot, temp_slider, max_tokens_slider, endpoint, token], chatbot
    )

    btn.click(clear_history, chatbot, chatbot)

# COMMAND ----------

dbx_app.mount_gradio_app(gr.routes.App.create_app(demo))

# COMMAND ----------

import nest_asyncio
nest_asyncio.apply()
dbx_app.run()

# COMMAND ----------