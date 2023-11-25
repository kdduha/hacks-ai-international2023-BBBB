import torch
import numpy as np
from transformers import (AutoTokenizer,
                          T5ForConditionalGeneration,
)


def upload_summary_model():
    summary_model_name = "IlyaGusev/rut5_base_sum_gazeta"
    summary_tokenizer = AutoTokenizer.from_pretrained(summary_model_name)
    summary_model = T5ForConditionalGeneration.from_pretrained(summary_model_name)
    return summary_tokenizer, summary_model


def summarize(text, summary_tokenizer, summary_model):
    input_ids = summary_tokenizer(
        text,
        max_length=600,
        add_special_tokens=True,
        padding="max_length",
        truncation=True,
        return_tensors="pt"
    )["input_ids"]

    output_ids = summary_model.generate(
        input_ids=input_ids,
        no_repeat_ngram_size=4
    )[0]

    summary = summary_tokenizer.decode(output_ids, skip_special_tokens=True)
    return summary


