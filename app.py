import hashlib
import logging
import os
from urllib.parse import urlparse

import validators
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
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


def get_valid_url(url: str):
    parsed_url = urlparse(url)
    if parsed_url.scheme not in ("https", "http", ""):
        return None
    if parsed_url.netloc == "" and parsed_url.path == "":
        return None
    if parsed_url.scheme == "":
        url = "https://" + url
    if not validators.url(url):
        return None
    return url


@app.post("/")
def add_url():
    url = request.form.get("url", "")
    validated_url = get_valid_url(url)
    if validated_url is None:
        flash("Please provide a valid URL")
        return render_template("homepage.html", url=url)
    url = validated_url

    keys = supabase.table("urls").select("key").eq("url", url).execute().data
    if len(keys) == 0:
        key = calc_key(url.encode())
        supabase.table("urls").insert({"key": key, "url": url}).execute()
    else:
        key = keys[0]["key"]  # type: ignore
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
    return redirect(url, code=301)


if __name__ == "__main__":
    app.run(debug=True)
