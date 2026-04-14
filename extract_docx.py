# -*- coding: utf-8 -*-
import sys
from docx import Document

doc = Document(r'D:\元气充能陪伴\论文框架.docx')
output = []

for para in doc.paragraphs:
    text = para.text.strip()
    if text:
        output.append(text)

result = '\n'.join(output)

# 保存到文件
with open(r'D:\元气充能陪伴\论文内容提取.txt', 'w', encoding='utf-8') as f:
    f.write(result)

print("[已保存到 论文内容提取.txt]")
print(f"共提取 {len(output)} 个段落")
