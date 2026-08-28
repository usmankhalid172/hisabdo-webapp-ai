"""
Expense Classification Model Fine-Tuning & Evaluation Script (Day 25 Part 2)
Project: HisabDo Web App AI
Intern: Rameesha Zafar
Task: Day 25 Part 2 - Expense Classification Model Fine-Tuning
"""

import os
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from sklearn.pipeline import Pipeline

def run_fine_tuning_and_evaluation():
    print("--- Starting Day 25 Part 2: Expense Classification Fine-Tuning ---")

    # Representative training dataset
    train_descriptions = [
        "Supermarket grocery purchase fresh vegetables milk",
        "Monthly house rent payment landlord transfer",
        "Uber ride fare to office transportation",
        "Electric utility bill payment K-Electric",
        "Dinner at restaurant food burger fries",
        "Doctor consultation fee medical clinic",
        "Pharmacy medicine purchase prescription drugs",
        "Gas station fuel refill petrol car",
        "Mobile recharge mobile phone package data",
        "Online grocery delivery vegetables fruits",
        "Apartment maintenance fee rent charges",
        "Taxi fare transport ride home"
    ]

    train_labels = [
        "Groceries", "Rent", "Transportation", "Utilities", "Food", 
        "Healthcare", "Healthcare", "Transportation", "Utilities", 
        "Groceries", "Rent", "Transportation"
    ]

    # Test dataset for edge cases and threshold evaluation
    test_descriptions = [
        "Grocery shopping for monthly provisions",
        "Office commute taxi fare",
        "Utility bill payment electric supply",
        "Pharmacy painkiller medicine",
        "Fast food lunch order pizza"
    ]
    test_labels = ["Groceries", "Transportation", "Utilities", "Healthcare", "Food"]

    # Build Pipeline with TF-IDF and Logistic Regression
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2))),
        ('clf', LogisticRegression(C=1.0, max_iter=200))
    ])

    print("\n[INFO] Training Logistic Regression Classifier...")
    pipeline.fit(train_descriptions, train_labels)

    print("\n[INFO] Evaluating Predictions & Confidence Thresholds...")
    probabilities = pipeline.predict_proba(test_descriptions)
    classes = pipeline.classes_
    
    confidence_threshold = 0.35
    predictions = []

    for idx, prob in enumerate(probabilities):
        max_idx = np.argmax(prob)
        max_prob = prob[max_idx]
        predicted_class = classes[max_idx]

        if max_prob < confidence_threshold:
            final_pred = "Uncategorized / Edge Case"
        else:
            final_pred = predicted_class

        predictions.append(final_pred)
        print(f"Sample: '{test_descriptions[idx]}'")
        print(f"  -> Predicted: {predicted_class} (Confidence: {max_prob:.4f}) | Final Output: {final_pred}")

    acc = accuracy_score(test_labels, predictions)
    print(f"\n--- Evaluation Results ---")
    print(f"Model Accuracy: {acc * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(test_labels, predictions, zero_division=0))

if __name__ == "__main__":
    run_fine_tuning_and_evaluation()