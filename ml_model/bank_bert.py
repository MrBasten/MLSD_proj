import torch

class BankBert:
    def __init__(self, model, tokenizer, le):
        self.model = model
        self.tokenizer = tokenizer
        self.le = le
        
    def eval_net(self, reports):
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(device)
        results = []
        for report in reports:
            tokenized_input = self.tokenizer(report, return_tensors='pt', truncation=True, max_length=512)
            input_ids = tokenized_input['input_ids'].to(device)
            attention_mask = tokenized_input['attention_mask'].to(device)

            self.model.eval()
            with torch.no_grad():
                logits = self.model(input_ids, attention_mask=attention_mask).logits

            quest_label = torch.argmax(logits, dim=1).item()
            pred_class = self.le.classes_[quest_label]

            results.append(pred_class)
        return results
