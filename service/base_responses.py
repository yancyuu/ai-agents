from fastapi import Request, JSONResponse
from service import error_codes

# 使用 FastAPI 的 JSONResponse 替代 Flask 的 jsonify
async def jsonify_response(data=None, status_response=None):
    if data is None:
        data = {}
    if status_response is None:
        status_response = {
            "errcode": error_codes.SUCCESS[0],
            "errmsg": error_codes.SUCCESS[1]
        }
    else:
        status_response = {
            "errcode": status_response[0],
            "errmsg": status_response[1]
        }
    ret = {}
    if data:
        ret = {
            "data": data
        }
    ret.update(**status_response)
    # 返回 JSONResponse 对象
    return JSONResponse(content=ret)

# 获取请求数据的函数
async def get_from_request(request: Request, key: str, default=None):
    val = default
    # 由于 FastAPI 的 Request 对象处理异步，需要使用 await
    if await request.json():
        val = (await request.json()).get(key)
    if request.query_params:
        val = request.query_params.get(key)
    return val
