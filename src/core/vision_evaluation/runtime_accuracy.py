class RuntimeAccuracy:
    """
    Computes comparative accuracy measurements between runtime observations and ground truth targets.
    """
    @staticmethod
    def evaluate_classification(prediction: str, ground_truth: str, confidence: float) -> dict:
        """
        Evaluate single string classification (e.g. Scene ID).
        """
        correct = (prediction.lower() == ground_truth.lower())
        score = 1.0 if correct else 0.0
        return {
            "prediction": prediction,
            "confidence": float(confidence),
            "ground_truth": ground_truth,
            "correct": correct,
            "score": score
        }

    @staticmethod
    def evaluate_set(predictions: list, ground_truth: list) -> dict:
        """
        Evaluate list-based detections (e.g. materials, subjects, edges).
        Calculates precision, recall, and F1.
        """
        preds = set(p.lower() for p in predictions)
        gts = set(g.lower() for g in ground_truth)
        
        tp = preds.intersection(gts)
        fp = preds - gts
        fn = gts - preds
        
        precision = len(tp) / len(preds) if len(preds) > 0 else (1.0 if len(gts) == 0 else 0.0)
        recall = len(tp) / len(gts) if len(gts) > 0 else 1.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        
        return {
            "predictions": predictions,
            "ground_truth": ground_truth,
            "tp": list(tp),
            "fp": list(fp),
            "fn": list(fn),
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "correct": (len(fp) == 0 and len(fn) == 0),
            "score": f1
        }
