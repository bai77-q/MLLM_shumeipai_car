import requests
import base64
from openai import OpenAI
import httpx
API_BASE = "https://api.lingyiwanwu.com/v1"
API_KEY = "013565e5b3154a8cb5f91e7113dbc04a"
client = OpenAI(
  api_key=API_KEY,
  base_url=API_BASE
)

# 系统提示词
SYSTEM_PROMPT = '''

我即将说一句给智能车的指令，你帮我从这句话中提取出目标物体，并从这张图中找到是否具有目标物体。如果有，则给出我抵达该目标物体的路线；如果没有，也请给出操作指令。

例如，如果我的指令是：请帮助我找到一个垃圾桶。
你输出这样的格式：
{
 "目标物体": "垃圾桶",
 "是否含有目标物体": "否",
 "操作指令": "前进50厘米，左转90度，前进20厘米"
}

只回复json本身即可，不要回复其它内容

我现在的指令是：
'''

PROMPT = '帮我找到一个红色的椅子'

image_path = "test.png"
with open(image_path, "rb") as image_file:
    image = "data:image/jpeg;base64," + base64.b64encode(image_file.read()).decode('utf-8')

completion = client.chat.completions.create(
  model="yi-vision",
  messages=[
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": SYSTEM_PROMPT + PROMPT
        },
        {
          "type": "image_url",
          "image_url": {
            "url": image
          }
        }
      ]
    },
  ]
)
print(completion)