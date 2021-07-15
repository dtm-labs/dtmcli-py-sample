from flask import Flask
from dtmcli import tcc

app = Flask(__name__)

@app.post("/api/TransOutTry")
def trans_out_try():
    return {"result": "SUCCESS"}

@app.post("/api/TransOutConfirm")
def trans_out_confirm():
    return {"result": "SUCCESS"}

@app.post("/api/TransOutCancel")
def trans_out_cancel():
    return {"result": "SUCCESS"}

@app.post("/api/TransInTry")
def trans_in_try():
    return {"result": "SUCCESS"}

@app.post("/api/TransInConfirm")
def trans_in_confirm():
    return {"result": "SUCCESS"}

@app.post("/api/TransInCancel")
def trans_in_cancel():
    return {"result": "SUCCESS"}

# 这是dtm服务地址
dtm = "http://localhost:8080/api/dtmsvr"
# 这是业务微服务地址
svc = "http://localhost:5000/api"

@app.get("/api/fireTcc")
def fire_tcc():
    # 发起tcc事务
    gid = tcc.tcc_global_transaction(dtm, tcc_trans)
    return {"gid": gid}

# tcc事务的具体处理
def tcc_trans(t):
    req = {"amount": 30} # 业务请求的负荷
    # 调用转出服务的Try|Confirm|Cancel
    t.call_branch(req, svc + "/TransOutTry", svc + "/TransOutConfirm", svc + "/TransOutCancel")
    # 调用转入服务的Try|Confirm|Cancel
    t.call_branch(req, svc + "/TransInTry", svc + "/TransInConfirm", svc + "/TransInCancel")
