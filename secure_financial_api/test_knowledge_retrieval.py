

from knowledge_retrieval import search_knowledge_base


def test_knowledge_retrieval():
    tests = [
        {
            "name": "Receivable definition",
            "question": "What does receivable mean?",
            "expected_id": "faq-001",
        },
        {
            "name": "Payable definition",
            "question": "What does payable mean?",
            "expected_id": "faq-002",
        },
        {
            "name": "Different wording about customer debt",
            "question": "What money do customers still owe my business?",
            "expected_id": "faq-006",
        },
        {
            "name": "Unrelated question uses safe fallback",
            "question": "What is the weather on Mars tomorrow?",
            "expected_id": None,
        },
        {
            "name": "Urdu-English mixed question",
            "question": "Mere customers ke paas mera kitna paisa baqi hai?",
            "expected_id": "faq-006",
        },
        {
            "name": "Outstanding customer debt question",
            "question": "What money is still outstanding?",
            "expected_id": "faq-006",
        },
    ]

    passed = 0
    total_checks = 0
    passed_checks = 0

    for test in tests:
        result = search_knowledge_base(test["question"])
        expected_id = test["expected_id"]

        if expected_id is None:
            checks = {
                "Safe fallback": result["found"] is False,
                "Fallback answer is not empty": bool(
                    result.get("answer", "").strip()
                ),
                "No source is falsely attributed": not result.get("source"),
            }
        else:
            checks = {
                "Correct FAQ retrieved": (
                    result["found"] is True
                    and result.get("document_id") == expected_id
                ),
                "Answer is not empty": bool(
                    result.get("answer", "").strip()
                ),
                "Source is provided": bool(
                    result.get("source", "").strip()
                ),
            }

        print(f"\nQuestion: {test['question']}")

        for check_name, success in checks.items():
            total_checks += 1
            if success:
                passed_checks += 1
                print(f"  PASS: {check_name}")
            else:
                print(f"  FAIL: {check_name}")

        assert all(checks.values()), (
            f"Failed checks for test case: {test['name']}"
        )

        passed += 1

        print(f"  Answer: {result.get('answer')}")
        print(f"  Source: {result.get('source') or 'No matching source'}")
        print(f"  Score: {result.get('score')}")

    print(f"\nTest cases passed: {passed}/{len(tests)}")
    print(f"Individual checks passed: {passed_checks}/{total_checks}")


if __name__ == "__main__":
    test_knowledge_retrieval()
