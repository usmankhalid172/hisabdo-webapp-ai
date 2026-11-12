
from text_chunks import (
    chunk_text,
    CHUNK_CONFIGS,
    encoding,
)


# Sample HisabDo content for testing
sample_texts = {
    "faq": (
        "How can I record business expenses? "
        "Open the expense section and select Add Expense. "
        "Enter the amount, date, category, and description. "
    ) * 100,

    "accounting_table": (
        "Feature | Description | Status\n"
        "Expense Tracking | Record business expenses | Active\n"
        "Sales Tracking | Monitor daily sales | Active\n"
        "Customer Payments | Track received payments | Active\n"
    ) * 100,

    "workflow": (
        "Step 1: Open the HisabDo dashboard.\n"
        "Step 2: Select the expense section.\n"
        "Step 3: Enter expense details.\n"
        "Step 4: Save the expense record.\n\n"
    ) * 100,

    "long_form": (
        "HisabDo is a business expense management platform. "
        "It helps business owners manage expenses, sales, "
        "customer payments, tasks, and business records. "
    ) * 100,
}


# Test all four content types
for content_type, text in sample_texts.items():

    chunks = chunk_text(
        text,
        document_id="hisabdo_test",
        page_number=1,
        content_type=content_type,
    )

    assert chunks, f"No chunks generated for {content_type}"

    max_tokens = CHUNK_CONFIGS[content_type]["chunk_size"]

    for index, chunk in enumerate(chunks):

        actual_tokens = len(encoding.encode(chunk["text"]))

        assert actual_tokens == chunk["token_count"]
        assert actual_tokens <= max_tokens
        assert chunk["document_id"] == "hisabdo_test"
        assert chunk["chunk_index"] == index
        assert chunk["page_number"] == 1
        assert chunk["content_type"] == content_type

    print(
        f"{content_type}: PASSED | "
        f"Chunks: {len(chunks)} | "
        f"Maximum tokens: {max_tokens}"
    )


# Test empty input
assert chunk_text("") == []

# Test invalid content type
try:
    chunk_text("Test content", content_type="invalid")
    raise AssertionError("Invalid content type was accepted")
except ValueError:
    print("Invalid content type: PASSED")


print("\nAll token-based chunking tests passed!")
