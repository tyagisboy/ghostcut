class ConfusionMatrix:
    """
    Generates and keeps track of confusion matrices for vision classifications
    (Scene, Subject, Hair, Material, Edge).
    """
    def __init__(self, categories: list):
        self.categories = categories
        # matrix structure: matrix[actual][predicted] = count
        self.matrix = {c: {c2: 0 for c2 in categories} for c in categories}

    def add_prediction(self, actual: str, predicted: str) -> None:
        if actual in self.matrix and predicted in self.matrix[actual]:
            self.matrix[actual][predicted] += 1

    def to_string(self) -> str:
        """
        Prints a text-aligned visual matrix table.
        """
        lines = []
        # Header
        header = f"{'Actual \\ Pred':<20}" + "".join(f"{c:>15}" for c in self.categories)
        lines.append(header)
        lines.append("-" * len(header))
        
        for act in self.categories:
            line = f"{act:<20}"
            for pred in self.categories:
                val = self.matrix[act][pred]
                line += f"{val:>15}"
            lines.append(line)
        return "\n".join(lines)
