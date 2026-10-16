
from knowledge_retrieval import search_knowledge_base


def run_tests():
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

    for test in tests:
        result = search_knowledge_base(test["question"])

        if test["expected_id"] is None:
            success = result["found"] is False
        else:
            success = (
                result["found"] is True
                and result.get("document_id") == test["expected_id"]
            )

        status = "PASS" if success else "FAIL"
        print(f"{status}: {test['name']}")
        print(f"  Question: {test['question']}")
        print(f"  Answer: {result['answer']}")
        print(f"  Source: {result.get('source') or 'No matching source'}")
        print(f"  Score: {result.get('score')}")
        print()

        if success:
            passed += 1

    print(f"Results: {passed}/{len(tests)} tests passed")


if __name__ == "__main__":
    run_tests()
