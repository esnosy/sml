import hashlib
import os
from urllib.parse import urlparse, urlunparse
import logging

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request
from supabase import create_client

load_dotenv(".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "")

supabase = create_client(
    os.environ.get("SUPABASE_URL", ""), os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
)


def calc_key(url: bytes):
    return hashlib.sha256(url).hexdigest()[:7]


def get_url(key: str):
    urls = supabase.table("urls").select("url").eq("key", key).execute().data
    if len(urls) == 0:
        return None
    return str(urls[0]["url"])  # type: ignore


@app.post("/")
def add_url():
    url = request.form.get("url")
    if url is None:
        flash("Please provide a URL")
        return render_template("homepage.html", url=url)
    parsed_url = urlparse(url, scheme="https")
    if parsed_url.scheme not in ("http", "https"):
        flash("Invalid URL, only http, https, and empty scheme are allowed")
        return render_template("homepage.html", url=url)
    url = urlunparse(parsed_url)
    key = calc_key(url.encode())
    if get_url(key) is None:
        supabase.table("urls").insert({"key": key, "url": url}).execute()
    return render_template(
        "shortened_url.html", shortened_url=f"https://sml-five.vercel.app/{key}"
    )


@app.get("/")
def homepage():
    return render_template("homepage.html")


@app.get("/<key>")
def redirect_to_page(key: str):
    url = get_url(key)
    if url is None:
        flash("URL doesn't exist")
        return redirect("/")
    return redirect(url)


if __name__ == "__main__":
    app.run(debug=True)
