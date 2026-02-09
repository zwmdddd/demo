from volcengine.visual.VisualService import VisualService  # 新增导入
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import time
import hmac
import hashlib
import json
import requests

load_dotenv()  # 加载.env文件中的环境变量
AK = os.getenv("VOLC_AK", "")  # 空字符串作为占位符，无真实密钥
SK = os.getenv("VOLC_SK", "")

app = Flask(__name__)
from flask_cors import CORS
CORS(app, resources={r"/*": {"origins": "*"}})


# 初始化即梦AI服务
visual_service = VisualService()
visual_service.set_ak(AK)
visual_service.set_sk(SK)

def generate_image_by_prompt(prompt):
    """
    调用即梦AI API生成图片
    :param prompt: 图片生成提示词
    :return: 图片URL或错误信息
    """
    try:
        # 1. 提交绘图任务
        submit_params = {
            "req_key": "high_aigen_general",  # 通用文生图接口
            "prompt": prompt,
            "width": 1024,                   # 图片宽度
            "height": 1024,                  # 图片高度
            "num": 1                         # 生成图片数量
        }
        submit_resp = visual_service.cv_sync2_async_submit_task(submit_params)

        # 获取任务ID
        task_id = submit_resp['data']['task_id']
        print(f"提交任务成功，Task ID: {task_id}")

        # 2. 轮询查询任务结果（异步等待生成完成）
        max_retries = 30  # 最大重试次数
        retry_interval = 2  # 每次重试间隔（秒）

        for _ in range(max_retries):
            get_result_params = {"task_id": task_id}
            result_resp = visual_service.cv_sync2_async_get_result(get_result_params)

            status = result_resp['data']['status']

            if status == 'success':
                # 任务成功，返回第一张图片URL
                image_urls = result_resp['data']['result']['image_urls']
                return {"success": True, "imageUrl": image_urls[0]}

            elif status == 'failed':
                return {"success": False, "message": f"任务失败：{result_resp['data'].get('error_msg', '未知错误')}"}

            # 任务还在运行，等待后重试
            time.sleep(retry_interval)

        # 超时
        return {"success": False, "message": "图片生成超时，请稍后重试"}

    except Exception as e:
        return {"success": False, "message": f"API调用异常：{str(e)}"}

# 后端接口：处理图片生成请求
@app.route('/generate-image', methods=['POST'])
def generate_image():
    # 获取前端传递的提示词
    data = request.get_json()
    prompt = data.get('prompt', '')

    if not prompt:
        return jsonify({"success": False, "message": "提示词不能为空"})

    # 调用即梦AI生成图片
    result = generate_image_by_prompt(prompt)
    return jsonify(result)

# 提供前端页面访问
@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    # 创建static文件夹并将index.html放入其中
    import os
    if not os.path.exists('static'):
        os.makedirs('static')

    app.run(debug=True, host='0.0.0.0', port=5000)