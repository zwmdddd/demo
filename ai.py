from volcengine.visual.VisualService import VisualService
from flask import Flask, request, jsonify, send_file
from dotenv import load_dotenv
import os
import time

# 加载环境变量（确保.env文件和ai.py同目录）
load_dotenv()
AK = os.getenv("VOLC_AK", "")
SK = os.getenv("VOLC_SK", "")

# 初始化Flask应用
app = Flask(__name__)
# 配置跨域
from flask_cors import CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# 初始化即梦AI服务
visual_service = VisualService()
visual_service.set_ak(AK)
visual_service.set_sk(SK)

def generate_image_by_prompt(prompt):
    """调用即梦AI API生成图片"""
    try:
        # 提交绘图任务
        submit_params = {
            "req_key": "high_aigen_general",
            "prompt": prompt,
            "width": 1024,
            "height": 1024,
            "num": 1
        }
        submit_resp = visual_service.cv_sync2_async_submit_task(submit_params)
        task_id = submit_resp['data']['task_id']
        print(f"任务ID: {task_id}")

        # 轮询查询结果
        max_retries = 30
        retry_interval = 2
        for _ in range(max_retries):
            result_resp = visual_service.cv_sync2_async_get_result({"task_id": task_id})
            status = result_resp['data']['status']

            if status == 'success':
                image_urls = result_resp['data']['result']['image_urls']
                return {"success": True, "imageUrl": image_urls[0]}
            elif status == 'failed':
                err_msg = result_resp['data'].get('error_msg', '未知错误')
                return {"success": False, "message": f"任务失败：{err_msg}"}

            time.sleep(retry_interval)

        return {"success": False, "message": "生成超时（30秒），请重试"}
    except Exception as e:
        return {"success": False, "message": f"API调用异常：{str(e)}"}

# 核心接口：处理图片生成请求（前端调用的是/generate-image，这里要匹配）
@app.route('/generate-image', methods=['POST'])
def generate_image():
    data = request.get_json()
    prompt = data.get('prompt', '').strip()

    if not prompt:
        return jsonify({"success": False, "message": "提示词不能为空"})

    result = generate_image_by_prompt(prompt)
    return jsonify(result)

# 根路径：直接返回前端页面（无需static文件夹，更简单）
@app.route('/')
def index():
    # 读取前端HTML文件内容并返回（确保index.html和ai.py同目录）
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return """
        <h1>文件缺失</h1>
        <p>请将index.html放在和ai.py相同的文件夹下</p>
        """

if __name__ == '__main__':
    # 启动服务，确保端口5000，允许所有IP访问
    app.run(debug=True, host='0.0.0.0', port=5000)