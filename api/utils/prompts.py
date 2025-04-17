from typing import Dict


# Define default prompt templates
DEFAULT_SYSTEM_TEMPLATE = """\
Use the following context to answer a users question. If you cannot find the answer in the context, say you don't know the answer.

IMPORTANT: Format your response with your thinking process and final answer as follows:
1. First provide your reasoning process inside <think>...</think> tags
2. Then provide your final answer, either:
   - Using <answer>...</answer> tags (preferred)
   - Or simply provide the answer directly after your thinking section

For example:
<think>
I'm analyzing the question in relation to the context. The question asks about X, and in the context I see information about Y and Z, which relates to X in the following way...
</think>
<answer>
Based on the context, the answer is...
</answer>

Or alternatively:
<think>
I'm analyzing the question in relation to the context. The question asks about X, and in the context I see information about Y and Z, which relates to X in the following way...
</think>
Based on the context, the answer is...
"""

DEFAULT_USER_TEMPLATE = """\
Context:
{context}

Question:
{question}
"""
