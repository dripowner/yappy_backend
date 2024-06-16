import re
from typing import ClassVar

from transformers import BertForSequenceClassification, BertTokenizerFast


class Model:
    class_mapping: ClassVar[dict[int, str]] = {
        i: name
        for i, name in enumerate(
            [
                "act",
                "application",
                "arrangement",
                "bill",
                "contract",
                "contract offer",
                "determination",
                "invoice",
                "order",
                "proxy",
                "statute",
            ]
        )
    }

    def __init__(
        self,
        model_name: str = "Samoed/e5-small-hackaton",
        class_mapping: dict[int, str] | None = None,
        device: str = "cpu",
        max_seq_len: int = 512,
    ):
        self.model = BertForSequenceClassification.from_pretrained(model_name)
        self.tokenizer = BertTokenizerFast.from_pretrained(model_name)
        self.device = device

        self.model.to(device)
        self.class_mapping = class_mapping or self.class_mapping
        self.max_seq_len = max_seq_len

    def preprocess(self, text: str) -> list[str]:
        texts = []
        for paragraph in text.split("\n"):
            if len(paragraph) > 0:
                paragraph = paragraph.replace("\r", " ").replace("\t", " ")
                paragraph = re.sub(r"\s+", " ", paragraph)
                if len(paragraph.split(" ")) < 10:
                    continue
                texts.append(paragraph)
        return texts

    def predict(self, text: str) -> str:
        texts = ["query: " + t for t in self.preprocess(text)]

        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            add_special_tokens=True,
            max_length=self.max_seq_len,
            padding="max_length",
            return_token_type_ids=True,
            truncation=True,
        )
        inputs.to(self.device)
        outputs = self.model(**inputs)
        logits = outputs.logits.sum(axis=0)
        pred_label = logits.argmax().item()
        return self.class_mapping[pred_label]