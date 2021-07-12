from flask import Flask

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
    gid = tcc_global_transaction(dtm, tcc_trans)
    return {"gid": gid}

def tcc_trans(t):
    req = {"amount": 30}
    t.call_branch(req, svc + "/TransOutTry", svc + "/TransOutConfirm", svc + "/TransOutCancel")
    t.call_branch(req, svc + "/TransInTry", svc + "/TransInConfirm", svc + "/TransInCancel")

# 下面是id.py的部分
import requests

class IdGenerator(object):
  def __init__(self, parent_id = ""):
    self.parent_id = parent_id
    self.branch_id = 0
  def new_branch_id(self):
    if self.branch_id >= 99:
      raise Exception("branch_id should not larger than 99")
    if len(self.parent_id) >= 20:
      raise Exception("parent_id length should not larger than 20")
    self.branch_id += 1
    return "%s%02d" % (self.parent_id, self.branch_id)

def check_status(status_code):
  if status_code != 200:
    raise Exception("bad result")

def gen_gid(dtm):
  r = requests.get(dtm + "/newGid")
  check_status(r.status_code)
  return r.json()["gid"]

# 下面是tcc.py
import traceback
import sys
import json

class Tcc(object):
  def __init__(self, dtmUrl, gid):
    self.dtm = dtmUrl
    self.gid = gid
    self.id_generator = IdGenerator()
  def call_branch(self, body, tryUrl, confirmUrl, cancalUrl):
      branch_id = self.id_generator.new_branch_id()
      r = requests.post(self.dtm + "/registerTccBranch", json={
          "gid": self.gid,
          "branch_id": branch_id,
          "trans_type": "tcc",
          "status": "prepared",
          "data": json.dumps(body),
          "try": tryUrl,
          "confirm": confirmUrl,
          "cancel": cancalUrl,
      })
      check_status(r.status_code)
      return requests.post(tryUrl, json=body, params={
          "gid": self.gid,
          "trans_type": "tcc",
          "branch_id": branch_id,
          "branch_type": "try",
      })

def tcc_global_transaction(dtmUrl, tcc_cb):
    tcc = Tcc(dtmUrl, gen_gid(dtmUrl))
    tbody = {
        "gid": tcc.gid,
        "trans_type": "tcc",
    }
    try:
        r = requests.post(tcc.dtm + "/prepare", json=tbody)
        check_status(r.status_code)
        tcc_cb(tcc)
        r = requests.post(tcc.dtm + "/submit", json=tbody)
        check_status(r.status_code)
    except:
        traceback.print_exception(*sys.exc_info())
        r = requests.post(tcc.dtm + "/abort", json=tbody)
        check_status(r.status_code)
        return ""
    return tcc.gid

def tcc_from_req(dtmUrl, gid, branch_id):
    if dtmUrl == "" or gid == "" or branch_id == "":
        raise Exception("bad tcc req info: dtm %s gid %s branch_id %s" % (dtmUrl, gid, branch_id))
    tcc = Tcc(dtmUrl, gid)
    tcc.id_generator = IdGenerator(branch_id)
    return tcc
