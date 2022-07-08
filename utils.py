#%%
from sqlite3 import dbapi2 as sqlite3
import pandas as pd 
import datetime
from datetime import timedelta
from werkzeug.security import check_password_hash, generate_password_hash
import random
DATABASE = "ohh-web.db"
#%%
def get_user_info(user_id):
    con = sqlite3.connect(DATABASE)
    user = pd.read_sql("select * from user", con)
    con.close()
    
    user_id_list = user["user_id"].values
    
    if user_id in user_id_list:
        return user[user["user_id"]==user_id].reset_index(drop=True)
    else:
        return pd.DataFrame()

def update_user_info(data):
    con = sqlite3.connect(DATABASE)
    user_info = pd.read_sql("select * from user", con)
    
    
    user_id = data["user_id"]
    balance = int(data["balance"])
    role = data["role"]

    user_info.loc[user_info["user_id"]==user_id, "balance"] = balance     
    user_info.loc[user_info["user_id"]==user_id, "role"] = role  
    
    user_info.to_sql("user", con, if_exists="replace", index=False)
    con.close()    
    
def get_all_user_info():
    con = sqlite3.connect(DATABASE)
    user_info = pd.read_sql("select * from user", con)
    con.close()
    
    user_info = user_info.to_dict("records")
    for user in user_info:
        if user["role"]=="admin":
            user.update(option=dict(admin="selected"))
        elif user["role"]=="provider":
            user.update(option=dict(provider="selected"))
        elif user["role"]=="buyer":
            user.update(option=dict(buyer="selected"))  
        else:
            user.update(option=dict(none="selected"))

    return user_info

def regist_user(user_id, user_pw, user_name, user_email, user_store):
    user_df = pd.DataFrame([dict(
        user_id = user_id,
        name = user_name,
        email = user_email,
        store = user_store,
        pw = user_pw,
        balance=0,
        role=""
    )])
    
    con = sqlite3.connect(DATABASE)
    user_df.to_sql("user", con, if_exists="append", index=False)
    con.close()
    
def get_user_role(user:str):
    user_info = get_user_info(user)
    return user_info["role"][0]

def get_date(iso_date):
    iso_date = datetime.datetime.fromisoformat(iso_date)
    date = iso_date.strftime("%y-%m-%d")
    return date

def get_sales_data(database):
    cols  =["OrderId","Time","SalesPrice","Platform"]

    con = sqlite3.connect(database)
    pos = pd.read_sql("select * from pos", con)
    pos["Platform"] = "POS"
    baemin = pd.read_sql("select * from baemin", con)
    baemin["Platform"] = "배민"
    coupang = pd.read_sql("select * from coupang", con)
    coupang["Platform"] = "쿠팡"
    try:
        naver = pd.read_sql("select * from naver", con)
        naver["Platform"] = "네이버"
    except:
        naver = pd.DataFrame(columns = cols)
    con.close()

    sales = pd.concat([pos[cols], baemin[cols],coupang[cols], naver[cols]])
    sales["date"] = sales["Time"].apply(get_date)

    return sales

def get_daily_sales(sales_data:pd.DataFrame)-> pd.DataFrame:
    sales = sales_data
    daily_sales = sales[["date","SalesPrice"]].groupby("date").sum().reset_index()
    return daily_sales


def get_sales_detail_data(database):
    cols = ["OrderId", "Time", "Item", "Quantity", "SalesPrice", "Platform"]
    con = sqlite3.connect(database)
    pos_detail = pd.read_sql("select * from pos_detail", con)
    pos_detail["Platform"] = "POS"
    baemin_detail = pd.read_sql("select * from baemin_detail", con)
    baemin_detail["Platform"] = "배민"
    coupang_detail = pd.read_sql("select * from coupang_detail", con)
    coupang_detail["Platform"] = "쿠팡"
    try:
        naver_detail = pd.read_sql("select * from naver_detail", con)
        naver_detail["Platform"] = "네이버"
    except:
        naver_detail = pd.DataFrame(columns = cols)
    con.close()

    sales_detail = pd.concat([pos_detail[cols], baemin_detail[cols],coupang_detail[cols], naver_detail[cols]])
    sales_detail["date"] = sales_detail["Time"].apply(get_date)

    return sales_detail

def get_start_date(date:str)-> str:
    # date = "2021-07-12"
    date_datetime = datetime.datetime.fromisoformat(date)
    day = date_datetime.weekday() # 월요일 0부터 시작
    day_diff = day - 0
    start_date_datetime = date_datetime - timedelta(days=day_diff)
    start_date = start_date_datetime.strftime("%Y-%m-%d")

    return start_date


def add_date(date:str, diff:int)->str:
    date_datetime = datetime.datetime.fromisoformat(date)
    date_datetime = date_datetime + timedelta(days=diff)
    date_datetime = date_datetime.strftime("%Y-%m-%d")
    
    return date_datetime



def get_week_date(start_date:str)->dict:
    # start_date = "2021-07-12"
    week_date = {
        "mon" : start_date,
        "tue" : add_date(start_date, 1),
        "wed" : add_date(start_date, 2),
        "thu" : add_date(start_date, 3),
        "fri" : add_date(start_date, 4),
        "sat" : add_date(start_date, 5),
        "sun" : add_date(start_date, 6)
    }
    return week_date


def get_part_time_data(start_date:str, store:str)-> pd.DataFrame:
    # start_date = "2021-07-12"    
    end_date = add_date(start_date, 6)
    con = sqlite3.connect(DATABASE)
    data = pd.read_sql("""SELECT * FROM part_time""", con)
    con.close()
    
    # new_data = pd.DataFrame({
    #     "date":"2021-07-13",
    #     "name":"KKK",
    #     "start_time": "09:00",
    #     "end_time":"12:00"
    # }, index=[0])

    # data = data.append(new_data)
    # data = data.sort_values("date")
    # data = data.reset_index(drop=True)
    # data.to_sql("part_time", con, if_exists="replace", index=False)

    data = data[(data["date"]>=start_date) & (data["date"]<=end_date)]
    data = data[data["store"]==store]
    return data

def str_tdelta(tdelta):
    if tdelta =="":
        return ""
    # arbitrary number of seconds
    s = tdelta.total_seconds()
    # hours
    hours = s // 3600 
    # remaining seconds
    s = s - (hours * 3600)
    # minutes
    minutes = s // 60
    # total time
    return '{:02}:{:02}'.format(int(hours), int(minutes))
    

def time_delta(start_time, end_time, rest_time):
    if start_time =="" or end_time=="":
        tdelta = ""
    else:
        tdelta = datetime.datetime.strptime(end_time, "%H:%M") - datetime.datetime.strptime(start_time, "%H:%M")
        rest_hh, rest_mm = rest_time.split(":")
        rest_sec = (60*int(rest_hh) + int(rest_mm))*60
        rest_time_= datetime.timedelta(seconds=rest_sec)
        tdelta = tdelta- rest_time_
        
    return str_tdelta(tdelta)

def add_time(timeList):
    mysum = timedelta()
    for i in timeList:
        if i!="":
            (h, m) = i.split(':')
            d = datetime.timedelta(hours=int(h), minutes=int(m))
            mysum += d
    
    return str_tdelta(mysum)

def get_day_time(part_time_data:pd.DataFrame, day:int):
    part_time_data = part_time_data[part_time_data["day"]==day]
    if len(part_time_data)==0:
        day_start_time = ""
        day_end_time = ""
        day_tdelta=""
        day_resttime = ""
    else:
        day_start_time, day_end_time, day_tdelta, day_resttime = part_time_data.iloc[-1][["start_time","end_time", "time_delta","rest_time"]]
    return dict(day_start_time=day_start_time, day_end_time=day_end_time, day_tdelta=day_tdelta, day_resttime=day_resttime)

def preprocess_part_time_data(part_time_data:pd.DataFrame)->list:
    unique_names = list(set(part_time_data["name"]))
    unique_names.sort() # 가나다 순

    result = []
    for name in unique_names:
        time_data__personal = part_time_data[part_time_data["name"] == name]
        time_data__personal["day"] = time_data__personal["date"].apply(lambda x: datetime.datetime.fromisoformat(x).weekday())
        time_data__personal["time_delta"] = time_data__personal.apply(lambda x: time_delta(x["start_time"], x["end_time"],x["rest_time"]), axis=1)

        day_dict = {0:"mon", 1:"tue", 2:"wed", 3:"thu", 4:"fri", 5:"sat", 6:"sun"}
        
        time_data__personal_dict = {
            "name" : name,
            "weekly_time": add_time(time_data__personal["time_delta"].values)
        }
        
        for day_number in day_dict:
            day = day_dict[day_number]
            day_start = get_day_time(time_data__personal, day_number)["day_start_time"]
            day_end = get_day_time(time_data__personal, day_number)["day_end_time"]
            day_rest = get_day_time(time_data__personal, day_number)["day_resttime"]
            day_time = get_day_time(time_data__personal, day_number)["day_tdelta"]
            
            if not day_rest:
                day_resthh ="00"
                day_restmm ="00"
            else:
                day_resthh, day_restmm = day_rest.split(":")
                
            time_data__personal_dict.update(
                {
                    f"{day}_start" : day_start,
                    f"{day}_end": day_end,
                    f"{day}_rest":day_rest,
                    f"{day}_resthh":day_resthh,
                    f"{day}_restmm":day_restmm,
                    f"{day}_time":day_time
                }
            )            
            
        result.append(time_data__personal_dict)
    return result


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)+1):
        yield start_date + timedelta(n)


def delete_part_time(data):
    store = data["store"]
    name = data["name"]
    job_start = data["job_start"]
    job_end = data["job_end"]
    
    con = sqlite3.connect(DATABASE)
    exist_db = pd.read_sql("select * from part_time", con)
    mask = (exist_db["name"]==name) & (exist_db["store"]==store) & (exist_db["date"]>=job_start) & (exist_db["date"]<=job_end) 
    new_db = exist_db[~mask]
    
    new_db.to_sql("part_time", con, if_exists="replace", index=False )
    con.close()
    print("delete db")

def add_part_time_schedule(data):
    #print(data)
    store = data["store"]

    day_number = {0:"mon", 1:"tue", 2:"wed", 3:"thu", 4:"fri", 5:"sat", 6:"sun"}
    start_date = datetime.datetime.fromisoformat(data["job_start"])
    end_date = datetime.datetime.fromisoformat(data["job_end"])

    result = []
    for current_date in daterange(start_date, end_date):
        # todo
        day = current_date.weekday()

        if data[f"{day_number[day]}_start"]=="" and data[f"{day_number[day]}_end"]=="":
            rest_time =""
        else:
            rest_time ="00:00"            

        result.append(
        {
            "date": current_date.strftime("%Y-%m-%d"),
            "day":day,
            "name": data["name"],
            "start_time": data[f"{day_number[day]}_start"] ,
            "end_time": data[f"{day_number[day]}_end"],
            "rest_time": rest_time,
            "store": store
        }
        )
    
    
    if result:
        result = pd.DataFrame(result)

        con = sqlite3.connect(DATABASE)
        exist_result = pd.read_sql("select * from part_time", con)
        added_result = pd.concat([exist_result, result])
        added_result = added_result.drop_duplicates(["name","date","store"], keep="last")
        added_result.to_sql("part_time", con, if_exists="replace", index=False)
        con.close()

        print("DB Append Complete.")


def get_prev_week(start_date:str):
    start_date = datetime.datetime.fromisoformat(start_date)

    prev_week_start_date = start_date - timedelta(days=7)
    prev_week_start_date = prev_week_start_date.strftime("%Y-%m-%d")

    return prev_week_start_date

def get_next_week(start_date:str):
    start_date = datetime.datetime.fromisoformat(start_date)

    next_week_start_date = start_date + timedelta(days=7)
    next_week_start_date = next_week_start_date.strftime("%Y-%m-%d")

    return next_week_start_date

def update_parttime_db(data:dict):
    
    day_to_num ={"mon":0, "tue":1, "wed":2, "thu":3, "fri":4,"sat":5,"sun":6}

    start_date = data.get("start")
    start_date = datetime.datetime.fromisoformat(start_date)

    store = data["store"]
    
    # date	name	start_time	end_time
    result = []
    for k in data.keys():
        if "_" in k: #요일_start, end, resthh, restmm / store, start
            name, day_time = k.split(".")
            day , ser = day_time.split("_") # ser:start/end/rest type

            day_number = day_to_num[day]
            date = start_date + timedelta(days=day_number)
            date = date.strftime("%Y-%m-%d")
            
            
            result.append({"date":date, "day":day,"name":name, "ser":ser, "value":data[k]})
            
    if result:
        result = pd.DataFrame(result)

        row_index = set(result.set_index(["date","name"]).index)

        db = []
        for date, name in row_index:
            start_time = result[(result["date"]==date)&(result["name"]==name)&(result["ser"]=="start")]["value"].values[0]
            end_time = result[(result["date"]==date)&(result["name"]==name)&(result["ser"]=="end")]["value"].values[0]

            rest_hh = result[(result["date"]==date)&(result["name"]==name)&(result["ser"]=="resthh")]["value"].values[0]
            rest_mm = result[(result["date"]==date)&(result["name"]==name)&(result["ser"]=="restmm")]["value"].values[0]
            day = result[(result["date"]==date)&(result["name"]==name)&(result["ser"]=="restmm")]["day"].values[0]

            if not rest_hh:
                rest_hh ="00"
            if not rest_mm:
                rest_mm = "00"
                
            rest_time = f"{rest_hh.zfill(2)}:{rest_mm.zfill(2)}"
            

            db.append(
                {"date":date,
                "name":name,
                "start_time":start_time,
                "end_time":end_time,
                "rest_time":rest_time,
                "day":day
                }
            )


        db = pd.DataFrame(db)
        db = db.sort_values(["date","name"])
        db["store"]=store
        
        con = sqlite3.connect(DATABASE)
        exist_db = pd.read_sql("select * from part_time", con)
        added_db = pd.concat([exist_db, db])
        added_db = added_db.drop_duplicates(["name","date","store"], keep="last")
        added_db.to_sql("part_time", con, if_exists="replace", index=False)
        con.close()
        print("DB Updated")



def update_cart(user:str, item:dict):
    print("update cart", item)
    con = sqlite3.connect(DATABASE)
    items = dict(user=user, code=item["code"], quantity = item["quantity"], target_date=item["target_date"], store=item["store"])
    cart = pd.DataFrame([items])
    cart["cart_order_id"] = cart["user"] + "-" + cart["code"] + "-" + cart["target_date"] + "-"+ str(round(random.random()*10000000))
    cart.to_sql("cart", con, if_exists="append", index=False)
    con.close()
    
    print(f"{items['code']} cart updated!")
    

def get_user_cart(user:str):
    con = sqlite3.connect(DATABASE)
    cart = pd.read_sql("select * from cart",con)
    con.close()
    
    user_cart=cart[cart["user"]==user]
    items = get_items_by_user(user)
    
    user_cart = pd.merge(user_cart, items, left_on="code", right_on="code", how="left")
    user_cart = user_cart[user_cart["quantity"].apply(lambda x : int(x)>0)]
    
    return user_cart.to_dict("records")
    
def get_items_by_user(user:str):
    user_role = get_user_role(user)
    
    items = pd.read_csv("item.txt", sep="\t")
    items["code"] = items["코드"].astype(str)
    items["name"] = items["품명"]
    items["unit"] = items["단위"] 
    items["price"] = items["단가"].astype(int)
    items["LT"] = items["LT"]
    items["buy_price"] = items["소비자가"].astype(int)  

    items = items[["code","name","unit","LT","price","buy_price"]]
    
    if user_role=="admin":
        pass
    elif user_role=="provider":
        pass
    elif user_role=="buyer":
        items["price"]=items["buy_price"]
        
    con = sqlite3.connect(DATABASE)
    bookmark = pd.read_sql("select * from bookmark", con)
    user_bookmark = bookmark[bookmark["user_id"]==user]
    
    user_item = pd.merge(items, user_bookmark, how="left", left_on="code", right_on="item_code")
    user_item.loc[user_item.isna()["mark"]==True, "mark"]=-1
    
    con.close()
            
    return user_item
    
def get_items(user:str):
    items = get_items_by_user(user) 

    return items.to_dict("records")

def update_order_history(user:str):
    con = sqlite3.connect(DATABASE)
    cart = pd.read_sql("select * from cart", con)
    con.close()
    
    user_cart = cart[cart["user"]==user]
    items = get_items_by_user(user)

    
    user_cart = pd.merge(user_cart, items, left_on="code", right_on="code", how="left")
    user_cart = user_cart[user_cart["quantity"].apply(lambda x : int(x)>0)]
    user_cart["status"]="주문대기"
    user_cart["quantity"] = user_cart["quantity"].astype(int)
    user_cart["price"] = user_cart["price"].astype(int)
    
    # now = datetime.datetime.now()
    # user_cart["order_id"] = ["oid" + str(int(datetime.datetime.timestamp(now))) + str(x).zfill(4) for x in user_cart.index]

        
    columns=["날짜","매출처","품명","원산지","비고","수량","단위","단가","V","가액","세액","금액","status","user"]
    
    user_cart["날짜"] = user_cart["target_date"]
    user_cart["매출처"] = get_user_info(user)["store"][0]
    user_cart["품명"] = user_cart["name"]
    user_cart["원산지"] = "" #TODO:아이템 정보 추가
    user_cart["비고"] = "" #TODO:아이템 정보 추가
    user_cart["수량"] = user_cart["quantity"]
    user_cart["단위"] = user_cart["unit"]
    user_cart["단가"] = user_cart["price"]
    user_cart["V"] = ""
    user_cart["가액"] = "" #TODO:
    user_cart["세액"] = "" #TODO:
    user_cart["금액"] = user_cart["quantity"]*user_cart["price"]
    user_cart["status"] = user_cart["status"]
    user_cart["user"] = user
    
    user_cart = user_cart[columns]
    
#    order_history = user_cart
    
    con = sqlite3.connect(DATABASE)
    order_history = pd.read_sql("select * from order_history", con)
    order_history_columns = order_history.columns
    order_history_columns.to_list().remove("order_id")
    order_history_tmp = order_history[order_history_columns]
    order_history_tmp = pd.concat([order_history_tmp, user_cart])
    order_history_tmp["order_id"] = order_history_tmp["날짜"] + "-" + order_history_tmp.groupby("날짜").cumcount().astype(str).str.zfill(5)
    order_history_tmp.to_sql("order_history", con, if_exists="replace", index=False) 

    cursor = con.cursor()
    cursor.execute("DELETE FROM cart WHERE user=?;",(user,));
    con.commit()
    
    con.close()
    
def update_order_history_status(data):
    print(data)
    con = sqlite3.connect(DATABASE)
    order_history = pd.read_sql("select * from order_history", con)
    
    order_id = data["order_id"]
    status = data["status"]
    
    order_history.loc[order_history["order_id"]==order_id,"status"] = status
    
    order_history.to_sql("order_history", con, if_exists="replace", index=False)
    
    
        
def get_order_history(user:str, start_date, end_date):
    con = sqlite3.connect(DATABASE)
    order_history = pd.read_sql("select * from order_history", con)
    con.close()
    
    if start_date:
        order_history = order_history[order_history["날짜"] >= start_date]
        order_history = order_history[order_history["날짜"] <= end_date]
    # if store=="all":
    #     pass
    # else:
    #     order_history = order_history[order_history["store"]==store]
    
    user_role = get_user_role(user)
    if user_role =="admin" or user_role =="provider":
        pass
    else:
        order_history = order_history[order_history["user"]==user]

    # if len(order_history)==0:
    #     print("+"*80)
    #     print(order_history)
    #     print("+"*80)
    #     return [None]
    
    # order_history["total_price"] = order_history["quantity"] * order_history["price"]
    
    order_history = order_history.iloc[:500]
    order_history = order_history.to_dict("records")
    
    for item in order_history:
        if item["status"]=="주문완료":
            item["status"]=dict(option="", option2="", option3="selected")
        elif item["status"]=="주문진행":
            item["status"]=dict(option="", option2="selected", option3="")
        else:
            item["status"]=dict(option1="selected", option2="", option3="")

    return order_history

# def get_order_detail(order_id_hidden):
#     con = sqlite3.connect(DATABASE)
#     order_detail = pd.read_sql("select * from order_detail", con)
#     con.close()
    
#     order_detail = order_detail[order_detail["order_id_hidden"]==order_id_hidden]
#     order_detail = order_detail[order_detail["quantity"].apply(lambda x : int(x)>0)]
    
#     return order_detail.to_dict("records")



def get_part_time_dashboard(target_date:str):
    con = sqlite3.connect(DATABASE)
    part_time = pd.read_sql("select * from part_time", con)
    con.close()
    
    part_time = part_time[part_time["date"]==target_date]
    store_list = list(set(part_time["store"]))
    
    def time_to_float(hhmm:str):
        if ":" in hhmm:
            hh, mm = hhmm.split(":")
            return round(float(hh) + float(mm)/60)
        else:
            return ""
        
    part_time["start_time"] = part_time["start_time"].apply(lambda x : time_to_float(x))
    part_time["end_time"] = part_time["end_time"].apply(lambda x : time_to_float(x))

    part_time_dashboard = list()
    for store in store_list:
        part_time_by_store = part_time[part_time["store"]==store] 
        
        rows=[]
        for i, row in part_time_by_store.iterrows():
            name = row["name"]
            start_time = row["start_time"]
            end_time = row["end_time"]
            if start_time=="" or end_time=="":
                continue 
            rows.append(dict(name=name, start_time=start_time, end_time=end_time))
        part_time_dashboard.append(dict(store=store, rows=rows))
        
    return part_time_dashboard

def get_transaction(user, start_date, end_date):
    con = sqlite3.connect(DATABASE)
    order_history = pd.read_sql("select * from order_history", con)
    con.close()
    
    order_history = order_history[order_history["날짜"] >= start_date]
    order_history = order_history[order_history["날짜"] <= end_date]

    user_role = get_user_role(user)
    if user_role =="admin" or user_role =="provider":
        pass
    else:
        order_history = order_history[order_history["user"]==user]
        
    return order_history

def make_transaction_csv(user, start_date, end_date):
    con = sqlite3.connect(DATABASE)
    order_history = pd.read_sql("select * from order_history", con)
    con.close()
    
    order_history = order_history[order_history["날짜"] >= start_date]
    order_history = order_history[order_history["날짜"] <= end_date]

    user_role = get_user_role(user)
    if user_role =="admin" or user_role =="provider":
        pass
    else:
        order_history = order_history[order_history["user"]==user]
        
    order_history.to_csv("static/results/transaction.csv", encoding="utf-8-sig", index=False)
        
# def init_db(db_name):
#     # db_name = DATABASE
#     con = sqlite3.connect(db_name)

#     con.execute("""CREATE TABLE part_time
#     (date text, name text, start_time text, end_time text)
#     """)

#     con.commit()

#     con.close()

    # data = pd.read_sql("""select * from part_time""", con)
    # data = data[data["name"]!="노희중"]
    # data.to_sql("part_time", con, if_exists="replace", index=False)
    
    # df = pd.DataFrame([dict(
    #     user_id = "test",
    #     name = "test",
    #     email = "test",
    #     pw = "test"
    # )])
    
    # df.to_sql("user", con, index=False)
    
    # con = sqlite3.connect(DATABASE)
    # c = con.cursor()
    # c.execute("DELETE FROM order_detail;",);
    # con.commit()
    # con.close()
    
    # con = sqlite3.connect(DATABASE)
    # cursor = con.cursor()
    # cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    # cursor.fetchall()

#%%
#con = sqlite3.connect(DATABASE)
#cart = pd.read_sql("select * from cart", con)
#cart = pd.DataFrame(columns=["user","code","quantity","target_date","store"])
#cart.to_sql("cart", con,index=False, if_exists="replace")
# %%
def update_trans():
    con = sqlite3.connect(DATABASE)
    order_history = pd.read_sql("select * from order_history", con)

    cols = order_history.columns.to_list()
    trans = pd.read_csv("trans_22_02.txt", sep="\t")
    trans.columns
    trans[cols]
    
    order_history_tmp = pd.concat([trans, order_history])
    order_history_tmp["order_id"] = order_history_tmp["날짜"] + "-" + order_history_tmp.groupby("날짜").cumcount().astype(str).str.zfill(5)
    order_history_tmp.to_sql("order_history", con, if_exists="replace", index=False) 
    
    con.close()
    
def update_user_bookmark(user_id, item_code):
    con = sqlite3.connect(DATABASE)
    bookmark = pd.read_sql("select * from bookmark", con)
    
    other_user_bookmark = bookmark[bookmark["user_id"]!=user_id]
    user_bookmark = bookmark[bookmark["user_id"]==user_id]
    
    if len(user_bookmark.loc[user_bookmark["item_code"]==item_code, "mark"])==0:
        user_bookmark.loc[-1] = [user_id, item_code, 1]
        user_bookmark.reset_index(drop=True, inplace=True)
    else:
        user_bookmark.loc[user_bookmark["item_code"]==item_code, "mark"] *= -1

    new_bookmark = pd.concat([other_user_bookmark, user_bookmark])        
    new_bookmark.to_sql("bookmark", con, if_exists="replace", index=False)

    con.close()
    
    
def delete_user_cart(data):
    cart_order_id = data["cart_order_id"]

    con = sqlite3.connect(DATABASE)
    cart = pd.read_sql("select * from cart", con)
    cart = cart[cart["cart_order_id"]!=cart_order_id]
    cart.to_sql("cart",con, if_exists="replace",index=False)
    con.close()
    

def change_order_status_all(data):
    order_id_list = data["order_id"].split(",")
    order_status = data["status"]
    print(order_id_list)
    print(order_status)

    con = sqlite3.connect(DATABASE)
    order_history = pd.read_sql("select * from order_history", con)
    order_history.loc[order_history["order_id"].isin(order_id_list) , "status"] = order_status
    
    order_history.to_sql("order_history", con, if_exists="replace", index=False)    
    con.close()
    
# %%
