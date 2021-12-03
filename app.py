from flask import Flask
from flask import request
from dtmcli import tcc
from dtmcli import barrier
from dtmcli import utils
from dtmcli import saga
import pymysql

app = Flask(__name__)

dbconf = {"host": "localhost", "port": "3306", "user": "root", "password": ""}

def conn_new():
  print("connecting: ", dbconf)
  return pymysql.connect(host=dbconf["host"], user=dbconf["user"], password=dbconf["password"], database="").cursor()

def barrier_from_req(request):
  return barrier.BranchBarrier(request.args.get("trans_type"), request.args.get("gid"), request.args.get("branch_id"), request.args.get("branch_type"))


# 这是dtm服务地址
dtm = "http://localhost:36789/api/dtmsvr"
# 这是业务微服务地址
svc = "http://localhost:5000/api"

@app.get("/api/fireTcc")
def fire_tcc():
    # 发起tcc事务
    gid = tcc.tcc_global_transaction(dtm, utils.gen_gid(dtm), tcc_trans)
    return {"gid": gid}

# tcc事务的具体处理
def tcc_trans(t):
    req = {"amount": 30} # 业务请求的负荷
    # 调用转出服务的Try|Confirm|Cancel
    t.call_branch(req, svc + "/TransOutTry", svc + "/TransOutConfirm", svc + "/TransOutCancel")
    # 调用转入服务的Try|Confirm|Cancel
    t.call_branch(req, svc + "/TransInTry", svc + "/TransInConfirm", svc + "/TransInCancel")

@app.get("/api/fireSaga")
def fire_saga():
    req = {"amount": 30}
    s = saga.Saga(dtm, utils.gen_gid(dtm))
    s.add(req, svc + "/TransOutSaga", svc + "/TransOutCompensate")
    s.add(req, svc + "/TransInSaga", svc + "/TransInCompensate")
    s.submit()
    return {"gid": s.gid}

out_uid = 1
in_uid = 2

def tcc_adjust_trading(cursor, uid, amount):
  affected = utils.sqlexec(
    cursor, "update dtm_busi.user_account set trading_balance=trading_balance+%d	where user_id=%d and trading_balance + %d + balance >= 0" % (amount, uid, amount))
  if affected == 0:
    raise Exception("update error, maybe balance not enough")


def tcc_adjust_balance(cursor, uid, amount):
  utils.sqlexec(
    cursor, "update dtm_busi.user_account set trading_balance=trading_balance-%d, balance=balance+%d where user_id=%d" % (-amount, amount, uid))


def saga_adjust_balance(cursor, uid, amount):
  affected = utils.sqlexec(
    cursor, "update dtm_busi.user_account set balance=balance+%d where user_id=%d and balance >= -%d" % (amount, uid, amount))
  if affected == 0:
    raise Exception("update error, balance not enough")


@app.post("/api/TransOutTry")
def trans_out_try():
  with barrier.AutoCursor(conn_new()) as cursor:
    def busi_callback(c):
      tcc_adjust_trading(c, out_uid, -30)
    barrier_from_req(request).call(cursor, busi_callback)
  return {"dtm_result": "SUCCESS"}

@app.post("/api/TransOutConfirm")
def trans_out_confirm():
  with barrier.AutoCursor(conn_new()) as cursor:
    def busi_callback(c):
      tcc_adjust_balance(c, out_uid, -30)
    barrier_from_req(request).call(cursor, busi_callback)
  return {"dtm_result": "SUCCESS"}

@app.post("/api/TransOutCancel")
def trans_out_cancel():
  with barrier.AutoCursor(conn_new()) as cursor:
    def busi_callback(c):
      tcc_adjust_trading(c, out_uid, 30)
    barrier_from_req(request).call(cursor, busi_callback)
  return {"dtm_result": "SUCCESS"}

@app.post("/api/TransInTry")
def trans_in_try():
  # return {"dtm_result": "FAILURE"}
  with barrier.AutoCursor(conn_new()) as cursor:
    def busi_callback(c):
      tcc_adjust_trading(c, in_uid, 30)
    barrier_from_req(request).call(cursor, busi_callback)
  # return {"dtm_result": "FAILURE"}
  return {"dtm_result": "SUCCESS"}

@app.post("/api/TransInConfirm")
def trans_in_confirm():
  with barrier.AutoCursor(conn_new()) as cursor:
    def busi_callback(c):
      tcc_adjust_balance(c, in_uid, 30)
    barrier_from_req(request).call(cursor, busi_callback)
  return {"dtm_result": "SUCCESS"}

@app.post("/api/TransInCancel")
def trans_in_cancel():
  with barrier.AutoCursor(conn_new()) as cursor:
    def busi_callback(c):
      tcc_adjust_trading(c, in_uid, -30)
    barrier_from_req(request).call(cursor, busi_callback)
  return {"dtm_result": "SUCCESS"}

@app.post("/api/TransOutSaga")
def trans_out_saga():
  with barrier.AutoCursor(conn_new()) as cursor:
    def busi_callback(c):
      saga_adjust_balance(c, out_uid, -30)
    barrier_from_req(request).call(cursor, busi_callback)
  return {"dtm_result": "SUCCESS"}

@app.post("/api/TransOutCompensate")
def trans_out_compensate():
  with barrier.AutoCursor(conn_new()) as cursor:
    def busi_callback(c):
      saga_adjust_balance(c, out_uid, 30)
    barrier_from_req(request).call(cursor, busi_callback)
  return {"dtm_result": "SUCCESS"}

@app.post("/api/TransInSaga")
def trans_in_saga():
  # return {"dtm_result": "FAILURE"}
  with barrier.AutoCursor(conn_new()) as cursor:
    def busi_callback(c):
      saga_adjust_balance(c, in_uid, 30)
    barrier_from_req(request).call(cursor, busi_callback)
  # return {"dtm_result": "FAILURE"}
  return {"dtm_result": "SUCCESS"}

@app.post("/api/TransInCompensate")
def trans_in_compensate():
  with barrier.AutoCursor(conn_new()) as cursor:
    def busi_callback(c):
      saga_adjust_balance(c, in_uid, -30)
    barrier_from_req(request).call(cursor, busi_callback)
  return {"dtm_result": "SUCCESS"}

