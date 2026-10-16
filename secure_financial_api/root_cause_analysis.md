\# Root Cause Analysis — HisabDo AI Finance Assistant



\## 1. Purpose



This document records chatbot issues observed during user testing, their likely root causes, and recommended investigation steps.



\## 2. Observed Issues



\### Issue 1: Customer balance questions receive generic answers

\- \*\*Example:\*\* "How much do my customers owe me?"

\- \*\*Observed behaviour:\*\* The chatbot explains what a customer balance or receivable means instead of providing an account-specific amount.

\- \*\*Likely root cause:\*\* The chatbot may be retrieving general knowledge instead of securely retrieving the signed-in user's financial records.

\- \*\*Recommended fix:\*\* Route balance questions to an authenticated financial API. Verify account ownership and calculate totals from the correct records.

\- \*\*Verification:\*\* Test with accounts containing different balances and confirm that users cannot access another account's data.



\### Issue 2: Payment-recording questions are not handled

\- \*\*Example:\*\* "A customer owes me money. How do I record their payment?"

\- \*\*Observed behaviour:\*\* The chatbot says it can only provide information about the user's own account.

\- \*\*Likely root cause:\*\* The chatbot may lack a suitable workflow or tool for payment-recording guidance.

\- \*\*Recommended fix:\*\* Provide verified instructions for recording payments. If the chatbot is expected to perform actions, implement an authorized workflow with confirmation and validation.

\- \*\*Verification:\*\* Test guidance separately from actual payment creation.



\### Issue 3: Questions about external tools receive generic answers

\- \*\*Example:\*\* "How can I check my cash flow in Xero?"

\- \*\*Observed behaviour:\*\* The chatbot gives general Xero-related information instead of clarifying the user's needs or providing relevant guidance.

\- \*\*Likely root cause:\*\* The knowledge base may not contain a verified answer for the specific product or integration.

\- \*\*Recommended fix:\*\* Add verified product-specific documentation where supported. Otherwise, clarify the question or safely explain the limitation.

\- \*\*Verification:\*\* Test supported product questions and unrelated questions separately.



\### Issue 4: Conversation history disappears after reopening the app

\- \*\*Observed behaviour:\*\* Previous chatbot messages are no longer visible after closing and reopening the app.

\- \*\*Likely root cause:\*\* Conversation history may not be persisted or restored.

\- \*\*Recommended fix:\*\* Investigate conversation storage, user/session association, and history-loading behaviour.

\- \*\*Verification:\*\* Confirm that a user's conversation can be restored securely without exposing another user's messages.



\### Issue 5: Chatbot responses are sometimes slow

\- \*\*Observed behaviour:\*\* A response took noticeable time during testing.

\- \*\*Likely root cause:\*\* Not confirmed. Possible causes include model latency, network requests, or backend processing.

\- \*\*Recommended fix:\*\* Measure request timings and inspect application logs before choosing an optimization.

\- \*\*Verification:\*\* Record response times across repeated tests and identify where delays occur.



\## 3. Semantic Retrieval Test Results



The local retrieval prototype passed 6 out of 6 tests:

\- Receivable definition

\- Payable definition

\- Customer debt expressed in different wording

\- Safe fallback for an unrelated question

\- Urdu-English mixed question

\- Outstanding customer debt question



These results validate the tested prototype scenarios only. They do not prove that the live HisabDo chatbot is fixed or integrated.



\## 4. Limitations and Follow-up



\- Verify FAQ content and sources against official documentation before treating them as trusted product guidance.

\- Test retrieval with simple, detailed, ambiguous, and Urdu-English questions.

\- Investigate failed questions using logs and reproducible test cases.

\- Ensure private financial answers come from authenticated, account-scoped data sources.

\- Confirm changes in the actual application before claiming a live issue is resolved.



\## 5. Status



Initial root cause analysis documented. Root causes marked as likely or unconfirmed require investigation. Fixes and live-system verification remain pending.

