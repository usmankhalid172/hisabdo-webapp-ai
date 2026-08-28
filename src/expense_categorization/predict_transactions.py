import joblib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "model" / "expense_categorization_pipeline.pkl"


def load_model():
    return joblib.load(MODEL_PATH)


def predict_category(model, description):
    prediction = model.predict([description])[0]
    probabilities = model.predict_proba([description])[0]
    confidence = max(probabilities)

    return prediction, confidence


if __name__ == "__main__":
    model = load_model()

    test_cases = [
        ("KFC dinner", "Food"),
        ("McDonald's lunch", "Food"),

        ("Bought groceries from Imtiaz", "Groceries"),
        ("Milk and bread from supermarket", "Groceries"),

        ("Uber ride to university", "Transport"),
        ("Petrol from PSO", "Transport"),

        ("Electricity bill payment", "Utilities"),
        ("Gas bill payment", "Utilities"),

        ("Pharmacy medicine", "Healthcare"),
        ("Doctor consultation fee", "Healthcare"),

        ("Bought shoes from shopping mall", "Shopping"),
        ("Daraz shopping order", "Shopping"),

        ("Netflix subscription", "Entertainment"),
        ("Cinema movie ticket", "Entertainment"),

        ("University tuition fee", "Education"),
        ("Bought programming book", "Education"),

        ("Internet bill payment", "Bills"),
        ("Mobile phone bill", "Bills"),

        ("Miscellaneous expense", "Other"),
        ("General household expense", "Other"),
    ]

    correct = 0

    print("Day 17 Realistic Transaction Predictions")
    print("----------------------------------------")

    for description, expected in test_cases:
        predicted, confidence = predict_category(model, description)

        result = "CORRECT" if predicted == expected else "INCORRECT"

        if result == "CORRECT":
            correct += 1

        print(f"Transaction: {description}")
        print(f"Expected: {expected}")
        print(f"Predicted: {predicted}")
        print(f"Confidence: {confidence:.2f}")
        print(f"Result: {result}")
        print("-" * 40)

    total = len(test_cases)
    incorrect = total - correct
    accuracy = correct / total

    print("\nDay 17 Test Summary")
    print("-------------------")
    print(f"Correct: {correct}/{total}")
    print(f"Incorrect: {incorrect}/{total}")
    print(f"Test Accuracy: {accuracy:.2%}")