import os
import json
import sqlite3
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

# ----------------------------
# Setup
# ----------------------------

load_dotenv(override=True)

MODEL = "gpt-4.1-mini"
DB = "prices_2.db"

openai = OpenAI()

system_message = """
You are a helpful assistant for an airline called FlightAI.
Give short, courteous answers, no more than 1 sentence.
Always be accurate. If you don't know the answer, say so.
"""

# ----------------------------
# Database setup
# ----------------------------


def init_database():
    with sqlite3.connect(DB) as conn:

        cursor = conn.cursor()

        cursor.execute(
            "CREATE TABLE IF NOT EXISTS prices (city TEXT PRIMARY KEY, price REAL)"
        )

        conn.commit()


def seed_database():
    ticket_prices = {
        "london": 799,
        "paris": 899,
        "tokyo": 1420,
        "sydney": 2999,
    }

    for city, price in ticket_prices.items():
        set_ticket_price(city, price)


# ----------------------------
# Tools / functions
# ----------------------------


def get_ticket_price(city):
    print(f"DATABASE TOOL CALLED: Getting price for {city}", flush=True)

    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT price FROM prices WHERE city = ?",
            (city.lower(),),
        )

        result = cursor.fetchone()

    if result:
        return f"Ticket price to {city} is ${result[0]}"

    return "No price data available for this city."


def set_ticket_price(city, price):
    print(f"DATABASE TOOL CALLED: Setting price for {city} to {price}", flush=True)

    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO prices (city, price)
            VALUES (?, ?)
            ON CONFLICT(city)
            DO UPDATE SET price = ?
            """,
            (city.lower(), price, price),
        )
        conn.commit()

    return f"Ticket price for {city} has been updated to ${price}."


AVAILABLE_FUNCTIONS = {
    "get_ticket_price": get_ticket_price,
    "set_ticket_price": set_ticket_price,
}

# ----------------------------
# Tool schemas
# ----------------------------

get_price_function = {
    "name": "get_ticket_price",
    "description": "Get the price of a return ticket to the destination city.",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "The city that the customer wants to travel to",
            },
        },
        "required": ["city"],
        "additionalProperties": False,
    },
}

set_price_function = {
    "name": "set_ticket_price",
    "description": "Set or update the price of a return ticket to a destination city.",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "The city whose ticket price should be updated",
            },
            "price": {
                "type": "number",
                "description": "The new ticket price",
            },
        },
        "required": ["city", "price"],
        "additionalProperties": False,
    },
}

tools = [
    {"type": "function", "function": get_price_function},
    {"type": "function", "function": set_price_function},
]


# ----------------------------
# Tool handling
# ----------------------------


def handle_tool_calls(message):
    responses = []

    for tool_call in message.tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        print(f"TOOL REQUESTED: {function_name}", flush=True)
        print(f"ARGUMENTS: {arguments}", flush=True)

        function_to_call = AVAILABLE_FUNCTIONS.get(function_name)

        if function_to_call is None:
            result = f"Unknown tool: {function_name}"
        else:
            result = function_to_call(**arguments)

        responses.append(
            {
                "role": "tool",
                "content": result,
                "tool_call_id": tool_call.id,
            }
        )

    return responses


# ----------------------------
# Chat function
# ----------------------------


def chat(user_message, history):
    history = [{"role": item["role"], "content": item["content"]} for item in history]

    messages = (
        [{"role": "system", "content": system_message}]
        + history
        + [{"role": "user", "content": user_message}]
    )

    response = openai.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
    )

    while response.choices[0].finish_reason == "tool_calls":
        assisstant_message = response.choices[0].message

        tool_responses = handle_tool_calls(assisstant_message)

        messages.append(assisstant_message)
        messages.extend(tool_responses)

        response = openai.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
        )

    return response.choices[0].message.content

# ----------------------------
# Run app
# ----------------------------

if __name__ == "__main__":
    init_database()
    seed_database()
    
    gr.ChatInterface(
        fn=chat,
        type="messages",
        title="FlightAI"
    ).launch()