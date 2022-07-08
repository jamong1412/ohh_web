#%%
from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash, send_file
from werkzeug.security import check_password_hash, generate_password_hash
from utils import *
from io import StringIO
from flask import Response


DATABASE = "ohh-web.db"

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET","POST"])
def login():
    if session.get("user"):
        flash("이미 로그인 되어 있습니다.")
        return redirect(url_for('index'))
    
    if request.method=="POST":
        input_user_id = request.form["inputID"]
        user_info = get_user_info(input_user_id)
        if len(user_info)==0:
            flash("ID 가 존재하지 않습니다.")
        elif not check_password_hash(user_info["pw"][0], request.form["inputPassword"]):
            flash("비밀번호가 일치하지 않습니다.")
        else:
            session["user"] = input_user_id
            session["role"] = user_info["role"][0]
            session["store"] = user_info["store"][0]
            return redirect(url_for('index'))
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    flash("로그아웃 되었습니다.")
    session.pop("user",None)
    session.pop("role",None)
    session.pop("store",None)
    return redirect(url_for("login"))

@app.route("/register", methods=["GET","POST"])
def register():
    if session.get("user"):
        flash("이미 로그인 되어 있습니다.")
        return redirect(url_for("index"))
    if request.method == "POST":   
        user_id = request.form["inputID"]
        user_pw = request.form["inputPassword"]
        user_pw = generate_password_hash(user_pw)
        user_name = request.form["inputName"]
        user_email = request.form["inputEmail"]
        user_store = request.form["inputStore"]
        
        if len(get_user_info(user_id))>0:
            flash("ID가 이미 존재합니다.")
        elif request.form["inputPassword"] != request.form["inputPasswordConfirm"]:
            flash("비밀번호가 일치하지 않습니다.")
        else:
            regist_user(user_id, user_pw, user_name, user_email, user_store)
            
            return redirect(url_for("login"))
    
    return render_template("register.html")

@app.route("/hr/user_info", methods=["GET","POST"])
def edit_user_info():
    if not session.get("user"):
        return redirect(url_for("login"))

    if request.method=="GET":
        user_info = get_all_user_info()
        return render_template("user_info.html", user_info=user_info)
    elif request.method=="POST":
        data = request.form
        print(data)
        update_user_info(data)
        return redirect(url_for("edit_user_info"))
    
@app.route("/management/sales")
def manage_sales():
    if not session.get("user"):
        return redirect(url_for('login'))
        
    sales_data = get_sales_data(DATABASE)
    daily_sales = get_daily_sales(sales_data)

    sales_data = sales_data.sort_values("Time", ascending=False).iloc[:300]

    return render_template("매출내역.html", sales_data = sales_data.to_dict("records"))

@app.route("/management/detail_sales")
def manage_detail_sales():
    if not session.get("user"):
        return redirect(url_for('login'))
        
    sales_detail_data = get_sales_detail_data(DATABASE)
    sales_detail_data = sales_detail_data.sort_values("Time", ascending=False).iloc[:1000]
    return render_template("상세매출내역.html", sales_detail_data = sales_detail_data.to_dict("records"))

@app.route("/hr/time_weekly_management", methods=["GET"])
def manage_part_time_weekly():
    if not session.get("user"):
        return redirect(url_for('login'))
        
    data = request.args
    
    # 매장 정보 가져오기
    if not data.get("store"):
        store = "시청"
    else: 
        store = data["store"]
    
    # start date 부터 7일 간의 날짜 데이터 표기
    if not data.get("start"):
        start_date = get_start_date(datetime.datetime.today().strftime("%Y-%m-%d"))
    else:
        start_date = get_start_date(data.get("start"))

    if data.get("prev") == "1":
        start_date = get_prev_week(start_date)
    elif data.get("next")=="1":
        start_date = get_next_week(start_date)

    week_date = get_week_date(start_date)

    part_time_data = get_part_time_data(start_date, store)

    part_time_dict = preprocess_part_time_data(part_time_data)

    add__start_date = datetime.datetime.now().strftime("%Y-%m-%d")
    add__end_date = (datetime.datetime.now()+datetime.timedelta(days=365)).strftime("%Y-%m-%d") 

    return render_template("주간시간관리.html", week_date = week_date, part_time = part_time_dict,
                           add__start_date = add__start_date, add__end_date=add__end_date, store=store)

@app.route("/hr/add_time_weekly", methods=["GET","POST"])
def add_time_weekly():
    if not session.get("user"):
        return redirect(url_for('login'))
        
    if request.method=="POST":
        data = request.form
        #print(data)
        store = data["store"]
        
        # 데이터 오류 검사
        if data["job_start"] > data["job_end"]:
            flash("오류: 끝 날짜가 시작 날짜보다 빠릅니다.")
            return redirect(url_for("manage_part_time_weekly", store=store))

        add_part_time_schedule(data)
        
        return redirect(url_for('manage_part_time_weekly', store = store))
    else:
        return redirect(url_for('manage_part_time_weekly', store = "시청"))

@app.route("/hr/delete_time", methods=["GET","POST"])
def delete_time():
    print("app delete time ")
    if not session.get("user"):
        return redirect(url_for("login"))
    
    if request.method=="POST":
        data = request.form
        store = data["store"]

        # 데이터 오류 검사
        if data["job_start"] > data["job_end"]:
            flash("오류: 끝 날짜가 시작 날짜보다 빠릅니다.")
            return redirect(url_for("manage_part_time_weekly", store=store))
        
        delete_part_time(data)
        
        return redirect(url_for('manage_part_time_weekly', store = store))
    else:
        return redirect(url_for('manage_part_time_weekly', store = "시청"))
        

@app.route("/hr/update_time_weekly", methods=["GET","POST"])
def update_time_weekly():
    if not session.get("user"):
        return redirect(url_for('login'))
        
    if request.method=="POST": 
        data = request.form
        store = data["store"]
        # start date 부터 7일 간의 날짜 데이터 표기
        if not data.get("start"):
            start_date = get_start_date(datetime.datetime.today().strftime("%Y-%m-%d"))
        else:
            start_date = get_start_date(data.get("start"))

        # update db
        update_parttime_db(data)

        return redirect(url_for('manage_part_time_weekly', start=start_date, store=store))
    else:
        data = request.args
        store = data["store"]
        
        if not data.get("start"):
            start_date = get_start_date(datetime.datetime.today().strftime("%Y-%m-%d"))
        else:
            start_date = get_start_date(data.get("start"))
            if data.get("prev") == "1":
                start_date = get_prev_week(start_date)
            elif data.get("next") =="1":
                start_date = get_next_week(start_date)

        week_date = get_week_date(start_date)
        part_time_data = get_part_time_data(start_date, store)
        part_time_dict = preprocess_part_time_data(part_time_data)

        return render_template("주간시간관리_수정.html", week_date = week_date, part_time = part_time_dict, store=store)

@app.route("/order/", methods=["GET","POST"])
def order_ingredient():
    if not session.get("user"):
        return redirect(url_for('login'))
    
    items = get_items(session.get("user"))
    store = request.args.get("store")
    if not store:
        store="매장을 선택하세요."
        
    user = session.get("user")
    balance = get_user_info(user)["balance"][0]

    if request.method=="POST":
        now  = datetime.datetime.now().strftime("%H:%M")
        if now < "06:00" or now > "21:00":
            flash("주문 가능 시각은 06:00 ~ 21:00 입니다. 주문 필요 시 담당자에게 카톡 문의 하세요.")

        else:
            data = request.form
            update_cart(user = session["user"], item=data)
            flash(f"{data['name']} {data['quantity']}EA 장바구니 추가되었습니다.")
    
    return render_template("재료주문.html", items= items, store=store, balance=balance)

@app.route("/order_bookmark/", methods=["GET","POST"])
def order_ingredient_bookmark():
    if not session.get("user"):
        return redirect(url_for('login'))
    
    items = get_items(session.get("user"))
    items = [x for x in items if x["mark"]==1]
    
    store = request.args.get("store")
    if not store:
        store="매장을 선택하세요."
        
    user = session.get("user")
    balance = get_user_info(user)["balance"][0]

    if request.method=="POST":
        now  = datetime.datetime.now().strftime("%H:%M")
        if now < "06:00" or now > "21:00":
            flash("주문 가능 시각은 06:00 ~ 21:00 입니다. 주문 필요 시 담당자에게 카톡 문의 하세요.")

        else:
            data = request.form
            update_cart(user = session["user"], item=data)
            flash(f"{data['name']} {data['quantity']}EA 장바구니 추가되었습니다.")
    
    return render_template("재료주문_즐겨찾기.html", items= items, store=store, balance=balance)


@app.route("/order/shopping_cart" , methods=["GET","POST"])
def shopping_cart():
    if not session.get("user"):
        return redirect(url_for('login'))
        
    if request.method=="POST":
        data = request.form
        user = session["user"]
        delete_user_cart(data)

    user_cart = get_user_cart(session["user"])
    user = session["user"]
    balance = get_user_info(user)["balance"][0]
    
    return render_template("장바구니.html", user_cart=user_cart, balance=balance)


@app.route("/order/shopping_history", methods=["GET","POST"])
def shopping_history():
    if not session.get("user"):
        return redirect(url_for('login'))

    start_date = datetime.datetime.now().strftime("%Y-%m-%d")
    end_date = datetime.datetime.now().strftime("%Y-%m-%d")

    if request.method=="POST":
        data = request.form

        start_date = data["start_date"]
        end_date = data["end_date"]

        if data.get("order_id"): # status 업데이트
            update_order_history_status(data)

    if request.method=="GET":    
        pass
        
    
    user = session["user"]
    order = get_order_history(user, start_date, end_date)
            
    return render_template("주문내역.html", order_list=order, start_date=start_date, end_date=end_date)
        
@app.route("/hr/time_table")
def time_table_dashboard():
    if not session.get("user"):
        return redirect(url_for("login"))
    
    if request.method=="GET":
        data = request.args
        if not data.get("target_day"):
            target_day = datetime.datetime.today().strftime("%Y-%m-%d")
        else:
            target_day = data["target_day"]
            
            if data.get("prev")=="1":
                target_day = target_day - 1
            elif data.get("next")=="1":
                target_day = target_day + 1
            
        part_time_dashboard = get_part_time_dashboard(target_day)
    
    return render_template("time_table_dashboard.html", part_time_dashboard=part_time_dashboard)
            

@app.route('/csv_file_download_with_stream')
def csv_file_download_with_stream():
    output_stream = StringIO()## dataframe을 저장할 IO stream 
    data = request.form
    start_date = data["start_date"]
    end_date = data["end_date"]
    df = get_transaction(start_date, end_date)
    df.to_csv(output_stream)## 그 결과를 앞서 만든 IO stream에 저장해줍니다. 
    filename = datetime.datetime.now().strftime("%Y-%m-%d")
    response = Response(
        output_stream.getvalue(), 
        mimetype='text/csv', 
        content_type='application/octet-stream',
    )
    response.headers["Content-Disposition"] = f"attachment; filename={download}.csv"
    return response 

from flask import send_file

@app.route('/csv_file_download_with_file', methods=["GET"])
def csv_file_download_with_file():
    
    data = request.args
    start_date = data["start_date"]
    end_date = data["end_date"]
    user = session["user"]
    make_transaction_csv(user, start_date, end_date)

    filename = datetime.datetime.now().strftime("%Y-%m-%d")

    file_name = f"static/results/transaction.csv"
    return send_file(file_name,
                     mimetype='text/csv',
                     attachment_filename=f'{filename}.csv',# 다운받아지는 파일 이름. 
                     as_attachment=True)

@app.route("/send_order")
def send_order():
    print("="*80)
    print("send_order")

    now  = datetime.datetime.now().strftime("%H:%M")
    if now < "06:00" or now > "21:00":
        flash("주문 가능 시각은 06:00 ~ 21:00 입니다. 주문 필요 시 담당자에게 카톡 문의 하세요.")
    else:
        update_order_history(session["user"])

    return redirect(url_for("shopping_history"))
    

@app.route("/update_bookmark")
def update_bookmark():
    if not session.get("user"):
        return redirect(url_for("login"))
    
    data = request.args
    item_code = data["code"]
    user_id = session.get("user")
    update_user_bookmark(user_id, item_code)
    
    if data["bookmark"]=="1":
        return redirect(url_for("order_ingredient_bookmark"))
    else:
        return redirect(url_for("order_ingredient"))
    
    
@app.route("/order/change_status", methods=["GET","POST"])
def change_order_status():
    if not session.get("user"):
        return redirect(url_for("login"))
    

    start_date = datetime.datetime.now().strftime("%Y-%m-%d")
    end_date = datetime.datetime.now().strftime("%Y-%m-%d")

    if request.method == "POST":
        data = request.form
        
        change_order_status_all(data)
        
        start_date = data["start_date"]
        end_date = data["end_date"]
            
    user = session.get("user")
    order = get_order_history(user, start_date, end_date)
    
    return render_template("주문내역.html", order_list = order, start_date = start_date, end_date=end_date)

if __name__=="__main__":
    app.secret_key = "superSecrectKey"
    app.run(host="127.0.0.1", port=5000, use_reloader=True, debug=True)







# %%

# %%

# %%
