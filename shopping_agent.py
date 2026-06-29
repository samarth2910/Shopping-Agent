import base64
import json
import os
import sqlite3
from typing import Optional

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

from reviews_api import get_product_rating, get_ratings_for_products

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "store.db")

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
vision_llm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", temperature=0)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
def search_products(query: str, max_price: Optional[float] = None, is_organic: Optional[bool] = None) -> str:
    """
    Search the product database by keyword (matched against name, description, and category).
    Optionally filter by maximum price and/or organic status.
    Returns a JSON array of matching products, each with: id, name, category, price,
    description, is_organic.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    sql = "SELECT id, name, category, price, description, is_organic FROM products WHERE 1=1"
    params: list = []

    if query:
        sql += " AND (name LIKE ? OR description LIKE ? OR category LIKE ?)"
        like = f"%{query}%"
        params.extend([like, like, like])

    if max_price is not None:
        sql += " AND price <= ?"
        params.append(max_price)

    if is_organic is not None:
        sql += " AND is_organic = ?"
        params.append(1 if is_organic else 0)

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    products = [
        {
            "id":          row[0],
            "name":        row[1],
            "category":    row[2],
            "price":       row[3],
            "description": row[4],
            "is_organic":  bool(row[5]),
        }
        for row in rows
    ]
    return json.dumps(products)


@tool
def get_rating(product_id: int) -> str:
    """
    Get the average customer rating and total review count for a product by its ID.
    Returns a JSON object with: product_id, average_rating, review_count.
    """
    return json.dumps(get_product_rating(product_id))


@tool
def get_ratings_batch(product_ids: list[int]) -> str:
    """
    Get ratings for multiple products in one call.
    Always prefer this over calling get_rating multiple times.
    Returns a JSON array with: product_id, average_rating, review_count.
    """
    return json.dumps(get_ratings_for_products(product_ids))


@tool
def checkout(product_id: int) -> str:
    """
    Place an order for the given product ID. Saves the order to the database and returns
    a confirmation message with the order ID, product name, and price.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, price FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return f"Error: product with ID {product_id} not found."

    name, price = row
    cursor.execute(
        "INSERT INTO orders (product_id, product_name, price, ordered_at) VALUES (?, ?, ?, datetime('now'))",
        (product_id, name, price),
    )
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return (
        f"Order #{order_id} confirmed! '{name}' has been successfully ordered for ${price:.2f}. "
        f"Your order will arrive in 3-5 business days. Thank you for shopping with us!"
    )


@tool
def get_order_history() -> str:
    """
    Retrieve all past orders placed by the user, most recent first.
    Call this when the user asks about previous orders, order history, or what they bought before.
    Returns a JSON array with: order_id, product_name, price, ordered_at.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, product_name, price, ordered_at FROM orders ORDER BY id DESC"
    )
    rows = cursor.fetchall()
    conn.close()

    return json.dumps([
        {"order_id": row[0], "product_name": row[1], "price": row[2], "ordered_at": row[3]}
        for row in rows
    ])


@tool
def save_preference(key: str, value: str) -> str:
    """
    Save a user preference permanently. 
    Keys: 'budget' (max price as number), 'organic' (true/false), 'min_rating' (number).
    Call this when the user expresses a preference like 'I only want organic' or 'keep under $20'.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_preferences (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value)
    )
    conn.commit()
    conn.close()
    return f"Got it! I've saved your preference: {key} = {value}"


@tool
def get_preferences() -> str:
    """
    Retrieve all saved user preferences (budget, organic, min_rating).
    ALWAYS call this before any product search to apply the user's default filters.
    Returns a JSON object like: {"budget": "20", "organic": "true", "min_rating": "4"}
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM user_preferences")
    rows = cursor.fetchall()
    conn.close()
    return json.dumps({row[0]: row[1] for row in rows})


@tool
def describe_product_image(image_path: str) -> str:
    """
    Analyze a product image and return its key attributes as a JSON object.
    Use this when the user uploads a photo of a product they are interested in.
    The returned attributes can be used directly with search_products.
    """
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    ext = os.path.splitext(image_path)[1].lower().lstrip(".")
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"

    message = HumanMessage(content=[
        {
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{image_data}"},
        },
        {
            "type": "text",
            "text": (
                "Look at this product image and extract its key attributes. "
                "Return ONLY a JSON object with these fields:\n"
                "- product_type: what kind of product it is (e.g. honey, olive oil, almonds)\n"
                "- search_query: a short keyword to search for it (e.g. 'honey', 'olive oil')\n"
                "- is_organic: true if the label says organic, false if not, null if unclear\n"
                "- description: one sentence describing the product"
            ),
        },
    ])

    response = vision_llm.invoke([message])
    return response.content


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

agent = create_agent(
    tools=[
        search_products,
        get_rating,
        get_ratings_batch,
        checkout,
        get_order_history,
        save_preference,
        get_preferences,
        describe_product_image,
    ],
    model=llm,
    system_prompt=(
        "You are a helpful shopping assistant. You ONLY help with shopping-related tasks "
        "such as searching products, viewing ratings, managing cart, and placing orders. "
        "If the user asks anything unrelated to shopping (e.g. coding, general knowledge, "
        "politics, math, personal advice), respond with exactly: "
        "'I'm a shopping assistant — I can only help with products, orders, and your cart.' "
        "Do not engage with off-topic requests under any circumstances.\n\n"

        "PREFERENCES — at the start of every search:\n"
        "1. Call get_preferences to load the user's saved filters.\n"
        "2. Apply budget as max_price, organic as is_organic, min_rating as rating filter.\n"
        "3. If the user says something like 'I prefer organic' or 'keep under $20' or "
        "   'I always want 4+ rated products', call save_preference to store it permanently "
        "   and confirm: 'Got it, I'll remember that for future searches.'\n\n"

        "IMAGE SEARCH — when the user provides an image path:\n"
        "1. Call describe_product_image with the path to identify the product.\n"
        "2. Use the returned search_query and is_organic to call search_products.\n"
        "3. Continue with the BROWSING flow from step 2 onwards.\n\n"

        "BROWSING — when the user describes what they want to buy:\n"
        "1. Call get_preferences first, then call search_products with those filters applied.\n"
        "2. Call get_ratings_batch with all product IDs at once (never call get_rating in a loop).\n"
        "3. Filter by min_rating if set in preferences or specified by user.\n"
        "4. Present qualifying products as a numbered list. For each item use this exact format "
        "   (plain text, no backticks, no code blocks, no bold, no italic):\n\n"
        "   #<number>. <name> (ID:<product_id>) — $<price> ★<rating> — <organic or non-organic>\n\n"
        "   Add a blank line between each product entry for readability. "
        "   Always include (ID:X) so you can reference it later.\n"
        "5. If only one product qualifies, still show it and ask: "
        "   'Would you like to order it? Just say yes or give me the number.'\n"
        "6. Do NOT call checkout at this stage.\n\n"

        "ORDER HISTORY — when the user asks about past orders, what they bought, or order history:\n"
        "1. Call get_order_history.\n"
        "2. Present as a numbered list: Order #ID — product name — $price — date.\n\n"

        "ORDERING — when the user confirms they want to buy:\n"
        "1. Look at your previous message to find the (ID:X) for the chosen product.\n"
        "2. Call checkout with that product_id.\n"
        "3. Confirm the order to the user in plain text.\n\n"

        "Never place an order unless the user explicitly confirms. "
        "Never guess a product_id — always take it from the (ID:X) in your own previous message."
    ),
)


if __name__ == "__main__":
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "I want to buy organic honey with 4.5+ rating and less than $20 price.",
                }
            ]
        }
    )
    print(result["messages"][-1].content)