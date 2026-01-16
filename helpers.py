from functools import wraps
from flask import session, redirect, render_template
import math

def login_required(f):
    """
    Decorator to require login for a route.
    Redirects to /login if user is not logged in.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorator to require admin role for a route.
    Assumes user is already logged in.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") != "admin":
            return redirect("/dashboard")
        return f(*args, **kwargs)
    return decorated_function


def apology(message, return_to="/"):
    return render_template(
        "apology.html",
        message=message,
        return_to=return_to
    )


def trait_vector(row):
    return [
        row["cleanliness"],
        row["sleep"],
        row["noise"],
        row["calls"],
        row["study"],
        row["sharing"],
        row["laundary"],
        row["language"]
    ]

def similarity(v1, v2):
    dist = math.sqrt(sum((v1[i] - v2[i]) ** 2 for i in range(len(v1))))
    return 1 / (1 + dist)

class DisjointSet:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        if x not in self.parent:
            self.parent[x] = x
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px != py:
            self.parent[py] = px



