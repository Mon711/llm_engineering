# Project - Airline AI Assistant

We'll now bring together what we've learned to make an AI Customer Support assistant for an Airline


```python
# imports

import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr
import sqlite3
```


```python
# Initialization

load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set")
    
MODEL = "gpt-4.1-mini"
openai = OpenAI()

DB = "prices.db"
```

    OpenAI API Key exists and begins sk-proj-



```python
system_message = """
You are a helpful assistant for an Airline called FlightAI.
Give short, courteous answers, no more than 1 sentence.
Always be accurate. If you don't know the answer, say so.
"""
```


```python
def get_ticket_price(city):
    print(f"DATABASE TOOL CALLED: Getting price for {city}", flush=True)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT price FROM prices WHERE city = ?', (city.lower(),))
        result = cursor.fetchone()
        return f"Ticket price to {city} is ${result[0]}" if result else "No price data available for this city"
```


```python
get_ticket_price("Paris")
```


```python
price_function = {
    "name": "get_ticket_price",
    "description": "Get the price of a return ticket to the destination city.",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city that the customer wants to travel to",
            },
        },
        "required": ["destination_city"],
        "additionalProperties": False
    }
}
tools = [{"type": "function", "function": price_function}]
tools
```


```python

def chat(message, history):
    history = [{"role": h["role"], "content": h["content"]} for h in history]
    messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model=MODEL, messages=messages)
    return response.choices[0].message.content

gr.ChatInterface(fn=chat, type="messages").launch()
```


```python
def chat(message, history):
    history = [{"role":h["role"], "content":h["content"]} for h in history]
    messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model=MODEL, messages=messages, tools=tools)

    while response.choices[0].finish_reason=="tool_calls":
        message = response.choices[0].message
        responses = handle_tool_calls(message)
        messages.append(message)
        messages.extend(responses)
        response = openai.chat.completions.create(model=MODEL, messages=messages, tools=tools)
    
    return response.choices[0].message.content
```


```python
def handle_tool_calls(message):
    responses = []
    for tool_call in message.tool_calls:
        if tool_call.function.name == "get_ticket_price":
            arguments = json.loads(tool_call.function.arguments)
            city = arguments.get('destination_city')
            price_details = get_ticket_price(city)
            responses.append({
                "role": "tool",
                "content": price_details,
                "tool_call_id": tool_call.id
            })
    return responses
```


```python
gr.ChatInterface(fn=chat, type="messages").launch()
```

## A bit more about what Gradio actually does:

1. Gradio constructs a frontend Svelte app based on our Python description of the UI
2. Gradio starts a server built upon the Starlette web framework listening on a free port that serves this React app
3. Gradio creates backend routes for our callbacks, like chat(), which calls our functions

And of course when Gradio generates the frontend app, it ensures that the the Submit button calls the right backend route.

That's it!

It's simple, and it has a result that feels magical.



# Let's go multi-modal!!

We can use DALL-E-3, the image generation model behind GPT-4o, to make us some images

Let's put this in a function called artist.

### Price alert: each time I generate an image it costs about 4 cents - don't go crazy with images!


```python
# Some imports for handling images

import base64
from io import BytesIO
from PIL import Image
```


```python
def artist(city):
    image_response = openai.images.generate(
            model="dall-e-3",
            prompt=f"An image representing a vacation in {city}, showing tourist spots and everything unique about {city}, in a vibrant pop-art style",
            size="1024x1024",
            n=1,
            response_format="b64_json",
        )
    image_base64 = image_response.data[0].b64_json
    image_data = base64.b64decode(image_base64)
    return Image.open(BytesIO(image_data))
```


```python
image = artist("Delhi, India")
display(image)
```


    ---------------------------------------------------------------------------

    BadRequestError                           Traceback (most recent call last)

    Cell In[14], line 1
    ----> 1 image = artist("Delhi, India")
          2 display(image)


    Cell In[9], line 2, in artist(city)
          1 def artist(city):
    ----> 2     image_response = openai.images.generate(
          3             model="dall-e-3",
          4             prompt=f"An image representing a vacation in {city}, showing tourist spots and everything unique about {city}, in a vibrant pop-art style",
          5             size="1024x1024",
          6             n=1,
          7             response_format="b64_json",
          8         )
          9     image_base64 = image_response.data[0].b64_json
         10     image_data = base64.b64decode(image_base64)


    File ~/Developer/forked-repos/llm_engineering/.venv/lib/python3.12/site-packages/openai/_utils/_utils.py:286, in required_args.<locals>.inner.<locals>.wrapper(*args, **kwargs)
        284             msg = f"Missing required argument: {quote(missing[0])}"
        285     raise TypeError(msg)
    --> 286 return func(*args, **kwargs)


    File ~/Developer/forked-repos/llm_engineering/.venv/lib/python3.12/site-packages/openai/resources/images.py:882, in Images.generate(self, prompt, background, model, moderation, n, output_compression, output_format, partial_images, quality, response_format, size, stream, style, user, extra_headers, extra_query, extra_body, timeout)
        854 @required_args(["prompt"], ["prompt", "stream"])
        855 def generate(
        856     self,
       (...)    880     timeout: float | httpx.Timeout | None | NotGiven = not_given,
        881 ) -> ImagesResponse | Stream[ImageGenStreamEvent]:
    --> 882     return self._post(
        883         "/images/generations",
        884         body=maybe_transform(
        885             {
        886                 "prompt": prompt,
        887                 "background": background,
        888                 "model": model,
        889                 "moderation": moderation,
        890                 "n": n,
        891                 "output_compression": output_compression,
        892                 "output_format": output_format,
        893                 "partial_images": partial_images,
        894                 "quality": quality,
        895                 "response_format": response_format,
        896                 "size": size,
        897                 "stream": stream,
        898                 "style": style,
        899                 "user": user,
        900             },
        901             image_generate_params.ImageGenerateParamsStreaming
        902             if stream
        903             else image_generate_params.ImageGenerateParamsNonStreaming,
        904         ),
        905         options=make_request_options(
        906             extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
        907         ),
        908         cast_to=ImagesResponse,
        909         stream=stream or False,
        910         stream_cls=Stream[ImageGenStreamEvent],
        911     )


    File ~/Developer/forked-repos/llm_engineering/.venv/lib/python3.12/site-packages/openai/_base_client.py:1259, in SyncAPIClient.post(self, path, cast_to, body, options, files, stream, stream_cls)
       1245 def post(
       1246     self,
       1247     path: str,
       (...)   1254     stream_cls: type[_StreamT] | None = None,
       1255 ) -> ResponseT | _StreamT:
       1256     opts = FinalRequestOptions.construct(
       1257         method="post", url=path, json_data=body, files=to_httpx_files(files), **options
       1258     )
    -> 1259     return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))


    File ~/Developer/forked-repos/llm_engineering/.venv/lib/python3.12/site-packages/openai/_base_client.py:1047, in SyncAPIClient.request(self, cast_to, options, stream, stream_cls)
       1044             err.response.read()
       1046         log.debug("Re-raising status error")
    -> 1047         raise self._make_status_error_from_response(err.response) from None
       1049     break
       1051 assert response is not None, "could not resolve response (should never happen)"


    BadRequestError: Error code: 400 - {'error': {'message': "Unknown parameter: 'response_format'.", 'type': 'invalid_request_error', 'param': 'response_format', 'code': 'unknown_parameter'}}



```python
def talker(message):
    response = openai.audio.speech.create(
      model="gpt-4o-mini-tts",
      voice="onyx",    # Also, try replacing onyx with alloy or coral
      input=message
    )
    return response.content
```

## Let's bring this home:

1. A multi-modal AI assistant with image and audio generation
2. Tool callling with database lookup
3. A step towards an Agentic workflow



```python
def chat(history):
    history = [{"role":h["role"], "content":h["content"]} for h in history]
    messages = [{"role": "system", "content": system_message}] + history
    response = openai.chat.completions.create(model=MODEL, messages=messages, tools=tools)
    cities = []
    image = None

    while response.choices[0].finish_reason=="tool_calls":
        message = response.choices[0].message
        responses, cities = handle_tool_calls_and_return_cities(message)
        messages.append(message)
        messages.extend(responses)
        response = openai.chat.completions.create(model=MODEL, messages=messages, tools=tools)

    reply = response.choices[0].message.content
    history += [{"role":"assistant", "content":reply}]

    voice = talker(reply)

    if cities:
        image = artist(cities[0])
    
    return history, voice, image

```


```python
def handle_tool_calls_and_return_cities(message):
    responses = []
    cities = []
    for tool_call in message.tool_calls:
        if tool_call.function.name == "get_ticket_price":
            arguments = json.loads(tool_call.function.arguments)
            city = arguments.get('destination_city')
            cities.append(city)
            price_details = get_ticket_price(city)
            responses.append({
                "role": "tool",
                "content": price_details,
                "tool_call_id": tool_call.id
            })
    return responses, cities
```

## The 3 types of Gradio UI

`gr.Interface` is for standard, simple UIs

`gr.ChatInterface` is for standard ChatBot UIs

`gr.Blocks` is for custom UIs where you control the components and the callbacks


```python
# Callbacks (along with the chat() function above)

def put_message_in_chatbot(message, history):
        return "", history + [{"role":"user", "content":message}]

# UI definition

with gr.Blocks() as ui:
    with gr.Row():
        chatbot = gr.Chatbot(height=500, type="messages")
        image_output = gr.Image(height=500, interactive=False)
    with gr.Row():
        audio_output = gr.Audio(autoplay=True)
    with gr.Row():
        message = gr.Textbox(label="Chat with our AI Assistant:")

# Hooking up events to callbacks

    message.submit(put_message_in_chatbot, inputs=[message, chatbot], outputs=[message, chatbot]).then(
        chat, inputs=chatbot, outputs=[chatbot, audio_output, image_output]
    )

ui.launch(inbrowser=True, auth=("ed", "bananas"))
```

# Exercises and Business Applications

Add in more tools - perhaps to simulate actually booking a flight. A student has done this and provided their example in the community contributions folder.

Next: take this and apply it to your business. Make a multi-modal AI assistant with tools that could carry out an activity for your work. A customer support assistant? New employee onboarding assistant? So many possibilities! Also, see the week2 end of week Exercise in the separate Notebook.

<table style="margin: 0; text-align: left;">
    <tr>
        <td style="width: 150px; height: 150px; vertical-align: middle;">
            <img src="../assets/thankyou.jpg" width="150" height="150" style="display: block;" />
        </td>
        <td>
            <h2 style="color:#090;">I have a special request for you</h2>
            <span style="color:#090;">
                My editor tells me that it makes a HUGE difference when students rate this course on Udemy - it's one of the main ways that Udemy decides whether to show it to others. If you're able to take a minute to rate this, I'd be so very grateful! And regardless - always please reach out to me at ed@edwarddonner.com if I can help at any point.
            </span>
        </td>
    </tr>
</table>
