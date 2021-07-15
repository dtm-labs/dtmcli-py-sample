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

dtm = "http://localhost:8080/api/dtmsvr"
svc = "http://localhost:5000/api"

@app.get("/api/fireTcc")
def fire_tcc():
    gid = tcc.tcc_global_transaction(dtm, tcc_trans)
    return {"gid": gid}

def tcc_trans(t):
    req = {"amount": 30}
    t.call_branch(req, svc + "/TransOutTry", svc + "/TransOutConfirm", svc + "/TransOutCancel")
    t.call_branch(req, svc + "/TransInTry", svc + "/TransInConfirm", svc + "/TransInCancel")
