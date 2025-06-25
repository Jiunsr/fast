import openai

client = openai.OpenAI(
    api_key="sk-e45c8628ce394db9b46e1d576c84b5db",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

response = client.chat.completions.create(
    model="qwen-turbo",
    messages=[
        {
            "role": "user",
            "content": """
        请根据我提供的英文单词 syllable，完成以下任务，并仅返回标准 JSON 格式：
        1. 将单词按发音音节划分，拼写形式，用连字符连接，如 "e-ra-ser"（字段：syl）。
        2. 给出每个音节对应的美式 IPA 音标数组（字段：to_ipa）。
        3. 给出单词中每个字母与其对应的美式 IPA 音标的精确映射（字段：to_ipa_pro）。

        输出格式如下，ipa不要出现符号/：

        {
        "syl": "<按发音划分的拼写>",
        "to_ipa": [
            {"<音节1所对应的字母或字母组合>": "<音节IPA1>", "<音节2所对应的字母或字母组合>": "<音节IPA2>"}
        ],
        "to_ipa_pro": [
            {"<单个字母>": "<对应IPA音标>"}
        ]
        }

        不要添加解释说明，仅输出 JSON。
        """,
        }
    ],
    stream=False,
)

print(response.choices[0].message.content.strip())
