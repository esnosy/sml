import hashlib
import logging
import os

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from supabase import create_client

load_dotenv(".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "")

app.add_url_rule(
    "/favicon.ico",
    endpoint="favicon",
    redirect_to=url_for("static", filename="favicon.ico"),
)

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
        flash("Please enter a URL")
        return redirect("/")
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
    return redirect(url)


if __name__ == "__main__":
    app.run(debug=True)
