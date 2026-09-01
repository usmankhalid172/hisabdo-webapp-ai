import re
import pandas as pd


def clean_text(text):
    """
    Clean an expense description or merchant name.
    """
    if pd.isna(text):
        return ""

    text = str(text).lower()
    text = text.strip()
    text = re.sub(r"\s+", " ", text)

    return text


def normalize_merchant(merchant):
    """
    Normalize merchant names.
    """
    return clean_text(merchant)


def validate_amount(amount):
    """
    Convert the expense amount to a numeric value.
    Invalid values are returned as None.
    """
    try:
        amount = float(amount)

        if amount < 0:
            return None

        return amount

    except (ValueError, TypeError):
        return None


def prepare_expense_data(data):
    """
    Prepare expense data for the baseline model.
    """
    data = data.copy()

    if "expense_description" in data.columns:
        data["expense_description"] = data["expense_description"].apply(
            clean_text
        )

    if "merchant" in data.columns:
        data["merchant"] = data["merchant"].apply(
            normalize_merchant
        )

    if "amount" in data.columns:
        data["amount"] = data["amount"].apply(
            validate_amount
        )

    data = data.drop_duplicates()

    return data