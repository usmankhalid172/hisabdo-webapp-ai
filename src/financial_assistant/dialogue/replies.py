"""
replies.py - every sentence the transaction / account flows say, in English and Roman Urdu.

Templates (not the AI model) are used for these flows because they contain money:
the user must see exactly the numbers that were understood, nothing invented.
Urdu-script users are answered in Roman Urdu (same rule as the HisabDo system prompt).
"""
from decimal import Decimal

from .models import Language, Slots

T: dict[str, dict[Language, str]] = {
    "ask_amount": {Language.ENGLISH: "How much was it?",
                   Language.ROMAN_URDU: "Kitne paise the?"},
    "ask_amount_again": {Language.ENGLISH: "Sorry, I couldn't find one clear amount. Please send just the amount, e.g. 500.",
                         Language.ROMAN_URDU: "Maaf kijiye, ek wazeh amount nahi mila. Sirf amount bhej dein, jaise 500."},
    "ask_currency": {Language.ENGLISH: "Which currency? (e.g. PKR)",
                     Language.ROMAN_URDU: "Kaunsi currency? (jaise PKR)"},
    "ask_direction": {Language.ENGLISH: "Was this money you spent (expense) or money you received (income)?",
                      Language.ROMAN_URDU: "Yeh kharcha tha (paise diye) ya aamdani (paise mile)?"},
    "ask_category_expense": {Language.ENGLISH: "What was it for? e.g. {options}",
                             Language.ROMAN_URDU: "Yeh kharcha kis cheez ka tha? Jaise: {options}"},
    "ask_category_income": {Language.ENGLISH: "What was this income from? e.g. {options}",
                            Language.ROMAN_URDU: "Yeh aamdani kis cheez se thi? Jaise: {options}"},
    "ask_period": {Language.ENGLISH: "For which period? e.g. this month, last month, or a month name like September.",
                   Language.ROMAN_URDU: "Kis period ki? Jaise: is mahine, pichle mahine, ya mahine ka naam (September)."},
    "ask_account": {Language.ENGLISH: "Which account? {options}",
                    Language.ROMAN_URDU: "Kaunsa account? {options}"},
    "ask_change": {Language.ENGLISH: "What should I change in that entry: the amount, category or date? (or say 'delete')",
                   Language.ROMAN_URDU: "Us entry mein kya badalna hai: amount, category ya date? (ya 'delete' likhein)"},
    "no_entry_to_fix": {
        Language.ENGLISH: "I can only change entries confirmed in this chat, and I don't see one yet. "
                          "Please open the entry in the app to edit it, or tell me the new entry to add.",
        Language.ROMAN_URDU: "Main sirf woh entries badal sakta hoon jo is chat mein confirm hui hon, aur abhi koi nahi hai. "
                             "Entry ko app mein khol kar edit karein, ya nayi entry bata dein."},
    "confirm_expense": {Language.ENGLISH: "Please confirm this expense: {summary}. Save it? (yes / no)",
                        Language.ROMAN_URDU: "Yeh kharcha confirm karein: {summary}. Save karun? (haan / nahi)"},
    "confirm_income": {Language.ENGLISH: "Please confirm this income: {summary}. Save it? (yes / no)",
                       Language.ROMAN_URDU: "Yeh aamdani confirm karein: {summary}. Save karun? (haan / nahi)"},
    "confirm_update": {Language.ENGLISH: "Change the last entry ({old}) to: {summary}? (yes / no)",
                       Language.ROMAN_URDU: "Pichli entry ({old}) ko yeh kar dun: {summary}? (haan / nahi)"},
    "confirm_delete": {Language.ENGLISH: "Delete the entry {old}? (yes / no)",
                       Language.ROMAN_URDU: "Entry {old} delete kar dun? (haan / nahi)"},
    "confirm_again": {Language.ENGLISH: "Please reply yes to save or no to cancel. {question}",
                      Language.ROMAN_URDU: "Save karne ke liye 'haan', cancel ke liye 'nahi' likhein. {question}"},
    "done_create": {
        Language.ENGLISH: "Done: {summary}. It is ready for the app to save to your records.",
        Language.ROMAN_URDU: "Ho gaya: {summary}. Yeh entry app ko aap ke record mein save karne ke liye bhej di gayi hai."},
    "done_update": {Language.ENGLISH: "Done. The change is ready for the app to apply: {summary}.",
                    Language.ROMAN_URDU: "Ho gaya. Tabdeeli app ko lagane ke liye bhej di gayi hai: {summary}."},
    "done_delete": {Language.ENGLISH: "Done. The app has been asked to delete the entry {old}.",
                    Language.ROMAN_URDU: "Ho gaya. App ko entry {old} delete karne ka keh diya gaya hai."},
    "cancelled": {Language.ENGLISH: "Okay, cancelled. Nothing was saved.",
                  Language.ROMAN_URDU: "Theek hai, cancel kar diya. Kuch save nahi hua."},
    "nothing_to_confirm": {Language.ENGLISH: "There is nothing waiting for confirmation right now.",
                           Language.ROMAN_URDU: "Abhi koi cheez confirm hone ke liye nahi hai."},
    "too_many_turns": {Language.ENGLISH: "Let's start over. Please send the full entry in one message, e.g. 'Spent 500 on petrol today'.",
                       Language.ROMAN_URDU: "Chaliye dobara shuru karte hain. Poori entry ek message mein bhejein, jaise 'Aaj 500 ka petrol dala'."},
    "replaced": {Language.ENGLISH: "(I dropped the unfinished entry and started this new one.) ",
                 Language.ROMAN_URDU: "(Pichli adhoori entry chhor kar nayi shuru ki.) "},
    "pending_reminder": {Language.ENGLISH: "Still waiting on your unfinished entry: {question}",
                         Language.ROMAN_URDU: "Aap ki adhoori entry abhi baqi hai: {question}"},
    "category_suggestion": {Language.ENGLISH: "That sounds like the category '{category}'.",
                            Language.ROMAN_URDU: "Yeh '{category}' category mein aata hai."},
    "category_unknown": {Language.ENGLISH: "I'm not sure which category fits. Common ones: {options}",
                         Language.ROMAN_URDU: "Pakka nahi keh sakta kaunsi category hogi. Aam categories: {options}"},
    "category_set": {Language.ENGLISH: "Category set to '{category}'.",
                     Language.ROMAN_URDU: "Category '{category}' kar di."},
    "no_account_data": {
        Language.ENGLISH: "I can't see your account data yet, so I won't guess any numbers. "
                          "You can check it in the app, or share the numbers here and I'll help with them.",
        Language.ROMAN_URDU: "Main abhi aap ka account data nahi dekh sakta, is liye koi number andaze se nahi bataunga. "
                             "App mein check kar lein, ya numbers yahan share karein, main madad karunga."},
    "account_data_error": {
        Language.ENGLISH: "I couldn't load your account data right now. Please try again in a moment.",
        Language.ROMAN_URDU: "Abhi aap ka account data load nahi ho saka. Thori dair baad dobara koshish karein."},
    "no_accounts": {Language.ENGLISH: "I don't see any account linked to you yet.",
                    Language.ROMAN_URDU: "Aap ke saath abhi koi account linked nahi hai."},
    "report": {
        Language.ENGLISH: "{account} ({period}{demo}): income {income}, expenses {expense}, net {net}{count}.{top}",
        Language.ROMAN_URDU: "{account} ({period}{demo}): aamdani {income}, kharcha {expense}, net {net}{count}.{top}"},
    "report_count": {Language.ENGLISH: ", {count} transactions", Language.ROMAN_URDU: ", {count} transactions"},
    "period_not_available": {
        Language.ENGLISH: "I can only show the current month's figures right now, not {period}. "
                          "Please check older periods in the app.",
        Language.ROMAN_URDU: "Abhi main sirf is mahine ke figures dikha sakta hoon, {period} ke nahi. "
                             "Purane periods app mein check karein."},
    "report_top": {Language.ENGLISH: " Biggest expense category: {category} ({amount}).",
                   Language.ROMAN_URDU: " Sab se zyada kharcha: {category} ({amount})."},
    "balance": {Language.ENGLISH: "{account}{demo}: balance {balance} (as of {as_of}).",
                Language.ROMAN_URDU: "{account}{demo}: balance {balance} ({as_of} tak)."},
}


def say(key: str, language: Language, **values) -> str:
    return T[key][language].format(**values)


def money(amount: Decimal | str | None, currency: str | None) -> str:
    if amount is None:
        return "?"
    value = Decimal(str(amount))
    text = f"{value:,.2f}" if value % 1 else f"{value:,.0f}"
    return f"{currency} {text}" if currency else text


def summary(slots: Slots, language: Language) -> str:
    parts = [money(slots.amount, slots.currency)]
    if slots.category:
        parts.append(slots.category)
    if slots.counterparty:
        parts.append(("to/from " if language == Language.ENGLISH else "") + slots.counterparty)
    if slots.date:
        parts.append(slots.date.strftime("%d %b %Y"))
    return ", ".join(parts)
