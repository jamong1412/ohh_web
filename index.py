# -*- coding: utf-8 -*-

#%%
from sqlite3 import dbapi2 as sqlite3
from hashlib import md5
from datetime import datetime
from contextlib import closing
from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash, send_file
from werkzeug.security import check_password_hash, generate_password_hash

import atexit


import numpy as np
import pandas as pd
import time




# configuration
# DATABASE = "ohhsalad.db"
PER_PAGE = 30
DEBUG = True
SECRET_KEY = "development key"


# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar("OHHSALAD_SETTINGS", silent=True)

@app.before_request
def before_request():
    g.user = None
    if "user_id" in session:
        g.user = "ohhsalad"


@app.route("/login", methods=["GET", "POST"])
def login():
    """Logs the user in."""
    if g.user:
        return redirect(url_for("home"))
    error = None
    if request.method == "POST":
        user = request.form["username"]
        if user != "ohhsalad":
            error = "Invalid username"
        elif request.form["password"] != "ohhsalad":
            error = "Invalid password"
        else:
            flash("You were logged in")
            session["user_id"] = user
            return redirect(url_for("home"))
    return render_template("login.html", error=error)

def read_db__shop1(date="2020-01-01T00:00:00"):
    DATABASE="ohhsalad.db"
    with sqlite3.connect(DATABASE) as con:
        pos = pd.read_sql("""select * from pos where time >=?""", con, params=(date,))
        pos_detail = pd.read_sql("""select * from pos_detail where time >=?""", con, params=(date,))
        pos["Platform"] = "POS"
        pos_detail["Platform"] = "POS"

        baemin = pd.read_sql("""select * from baemin where time >=?""", con, params=(date,))
        baemin_detail = pd.read_sql("""select * from baemin_detail where time >=?""", con, params=(date,))
        baemin["Platform"] = "배민"
        baemin_detail["Platform"] = "배민"

        coupang = pd.read_sql("""select * from coupang where time >=?""", con, params=(date,))
        coupang_detail = pd.read_sql("""select * from coupang_detail where time >=?""", con, params=(date,))
        coupang["Platform"] = "쿠팡"
        coupang_detail["Platform"] = "쿠팡"

        naver = pd.read_sql("""select * from naver where time >=?""", con, params=(date,))
        naver_detail = pd.read_sql("""select * from naver_detail where time >=?""", con, params=(date,))
        naver.columns = ["OrderId"] + list(naver.columns[1:].values)
        naver["Platform"] = "Naver"
        naver_detail["Platform"] = "Naver"

        # showing
        sales_cols = ["OrderId", "Time", "SalesPrice", "Platform"]
        sales = pd.concat([pos[sales_cols],baemin[sales_cols],coupang[sales_cols],naver[sales_cols]])
        sales = sales.sort_values("Time", ascending=False)
        
        sales_detail_cols = ["OrderId", "Time", "Item", "Quantity", "Platform"]
        sales_detail = pd.concat([pos_detail[sales_detail_cols],baemin_detail[sales_detail_cols],coupang_detail[sales_detail_cols],naver_detail[sales_detail_cols]])
        sales_detail = sales_detail.sort_values("Time", ascending=False)

        total_sales = sales["SalesPrice"].sum()

    return sales, sales_detail, total_sales
    

def read_db__shop2(date="2020-01-01T00:00:00"):
    DATABASE="ohhsalad_sr.db"
    with sqlite3.connect(DATABASE) as con:
        pos = pd.read_sql("""select * from pos where time >=?""", con, params=(date,))
        pos_detail = pd.read_sql("""select * from pos_detail where time >=?""", con, params=(date,))
        pos["Platform"] = "POS"
        pos_detail["Platform"] = "POS"

        baemin = pd.read_sql("""select * from baemin where time >=?""", con, params=(date,))
        baemin_detail = pd.read_sql("""select * from baemin_detail where time >=?""", con, params=(date,))
        baemin["Platform"] = "배민"
        baemin_detail["Platform"] = "배민"

        coupang = pd.read_sql("""select * from coupang where time >=?""", con, params=(date,))
        coupang_detail = pd.read_sql("""select * from coupang_detail where time >=?""", con, params=(date,))
        coupang["Platform"] = "쿠팡"
        coupang_detail["Platform"] = "쿠팡"

        # showing
        sales_cols = ["OrderId", "Time", "SalesPrice", "Platform"]
        sales = pd.concat([pos[sales_cols],baemin[sales_cols],coupang[sales_cols]])
        sales = sales.sort_values("Time", ascending=False)
        
        sales_detail_cols = ["OrderId", "Time", "Item", "Quantity", "Platform"]
        sales_detail = pd.concat([pos_detail[sales_detail_cols],baemin_detail[sales_detail_cols],coupang_detail[sales_detail_cols]])
        sales_detail = sales_detail.sort_values("Time", ascending=False)

        total_sales = sales["SalesPrice"].sum()

    return sales, sales_detail, total_sales
    

def to_tuple(df):
    result = []
    for j in range(len(df)):
        temp = []
        for key in df.to_dict("records")[j].keys():
            temp.append(df.to_dict("records")[j][key])
        result.append(tuple(temp))
    return result

@app.route("/")
def home():
    if not g.user:
        return redirect("login")

    today = datetime.today()
    today_isoformat = datetime(today.year, today.month, today.day, 0, 0, 0).isoformat()

    return render_template(
        "매출현황.html",
    )


@app.route("/shop1")
def shop1():
    if not g.user:
        return redirect("login")

    today = datetime.today()
    today_isoformat = datetime(today.year, today.month, today.day, 0, 0, 0).isoformat()

    sales, sales_detail, total_sales = read_db__shop1(today_isoformat)

    return render_template(
        "매출현황.html",
        total_sales = total_sales,
        items = sales.to_dict("records")
    )

@app.route("/shop2")
def shop2():
    if not g.user:
        return redirect("login")
    today = datetime.today()
    today_isoformat = datetime(today.year, today.month, today.day, 0, 0, 0).isoformat()

    sales, sales_detail, total_sales = read_db__shop2(today_isoformat)

    return render_template(
        "매출현황.html",
        total_sales = total_sales,
        items = sales.to_dict("records")
    )


@app.route("/export_sales_shop1")
def export_sales_shop1():
    if not g.user:
        return redirect("login")    
    try:
        sales, sales_detail, total_sales = read_db__shop1()
        sales = sales_parser(sales)
        sales.to_csv("./download/언주_매출.csv", sep=",", index=False, encoding="utf-8-sig")
        return send_file("./download/언주_매출.csv", mimetype="text/csv", attachment_filename=f"언주_매출.csv", as_attachment=True)
    except:
        return redirect("/")

@app.route("/export_sales_detail_shop1")
def export_sales_detail_shop1():
    if not g.user:
        return redirect("login")
    try:
        sales, sales_detail, total_sales = read_db__shop1()
        sales_detail = sales_parser(sales_detail)
        sales_detail.to_csv("./download/언주_매출상세.csv", sep=",", index=False, encoding="utf-8-sig")
        return send_file("./download/언주_매출상세.csv", mimetype="text/csv", attachment_filename=f"언주_매출상세.csv", as_attachment=True)
    except:
        return redirect("/")

@app.route("/export_sales_shop2")
def export_sales_shop2():
    if not g.user:
        return redirect("login")
    try:
        sales, sales_detail, total_sales = read_db__shop2()
        sales = sales_parser(sales)
        sales.to_csv("./download/선릉_매출.csv", sep=",", index=False, encoding="utf-8-sig")
        return send_file("./download/선릉_매출.csv", mimetype="text/csv", attachment_filename=f"선릉_매출.csv", as_attachment=True)
    except:
        return redirect("/")

@app.route("/export_sales_detail_shop2")
def export_sales_detail_shop2():
    if not g.user:
        return redirect("login")
    try:
        sales, sales_detail, total_sales = read_db__shop2()
        sales_detail = sales_parser(sales_detail)
        sales_detail.to_csv("./download/선릉_매출상세.csv", sep=",", index=False, encoding="utf-8-sig")
        return send_file("./download/선릉_매출상세.csv", mimetype="text/csv", attachment_filename=f"선릉_매출상세.csv", as_attachment=True)
    except:
        return redirect("/")

def sales_parser(sales):
    # sales["Time"] = sales["Time"].str.replace("T24","T12")
    sales["day"] = sales['Time'].map(lambda x : get_weekday(x))
    sales["Hours"] = sales["Time"].str[-5:-3].astype(int) 
    sales["date"] = sales["Time"].str[:10]

    return sales


def get_weekday(date):
    a = datetime.fromisoformat(date).weekday()
    days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    return days[a]



# %%

#%%
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, use_reloader=False)
    # app.run( port=5000, use_reloader=False)
#%%
# %%
# %%

# %%
