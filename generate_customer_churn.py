import json, random, sys

QUANTITIES = [250, 500, 1000]
COMPLAINT_TYPES_LOW = []
COMPLAINT_TYPES_MED = ["delivery delay", "refund delay"]
COMPLAINT_TYPES_HIGH = ["milk quality issue", "product defect", "refund delay", "multiple issues"]

ACTIONS = {
    1: "Maintain engagement with loyalty rewards or appreciation message.",
    2: "Offer moderate loyalty credits or targeted discounts to prevent churn.",
    3: "Immediate outreach from support with personalized discount or offer."
}

# OPENAI GPT-3.5 TURBO CONSTRAINTS:
# - Supports fine-tuning via OpenAI Fine-tuning API
# - Model ID: gpt-3.5-turbo
# - Format: Uses 'messages' format (required for chat models)
# - Token constraints: Each training example must fit within model context limit
# - Max context window: 4,096 tokens
TOTAL_RECORDS = 500  # Adjust based on your training needs
DISTRIBUTION = {1: 0.3, 2: 0.4, 3: 0.3}
TARGET_COUNTS = {score: int(TOTAL_RECORDS * frac) for score, frac in DISTRIBUTION.items()}

# OPENAI FORMAT:
# 'messages' - Required format for GPT-3.5 Turbo fine-tuning
# Each record must have a "messages" array with "role" and "content" fields
OPENAI_FORMAT = 'messages'  # Required for GPT-3.5 Turbo

# Approximate token estimation (1 token ≈ 4 characters for English)
TOKEN_TO_CHAR_RATIO = 4

def generate_customer_record(churn_score: int):
    quantity = random.choice(QUANTITIES)
    if churn_score == 1:
        duration_months = random.randint(5, 8)
        price_hike = random.choice([0, 3, 5])
        complaints = 0
        complaint_type = None
        last_purchase_gap = random.randint(0, 15)
        competitor_price_drop = False
        regularity = "regularly"
    elif churn_score == 2:
        duration_months = random.randint(3, 6)
        price_hike = random.randint(8, 12)
        complaints = random.choice([1, 2])
        complaint_type = random.choice(COMPLAINT_TYPES_MED)
        last_purchase_gap = random.randint(16, 30)
        competitor_price_drop = random.random() < 0.2
        regularity = random.choice(["regularly", "slightly irregularly"])
    else:  # churn_score == 3
        duration_months = random.randint(1, 4)
        price_hike = random.randint(13, 20)
        complaints = random.randint(2, 3)
        complaint_type = random.choice(COMPLAINT_TYPES_HIGH)
        last_purchase_gap = random.randint(31, 45)
        competitor_price_drop = random.random() < 0.6
        regularity = "irregularly"

    # Build description
    profile = f"Customer bought {quantity}ml {regularity} for {duration_months} months. "
    profile += f"Price increased by {price_hike}% recently. "
    if complaints > 0:
        profile += f"They raised {complaints} complaint(s) about {complaint_type}. "
    else:
        profile += "No complaints have been raised. "
    profile += f"Last purchase was {last_purchase_gap} days ago. "
    if competitor_price_drop:
        profile += "Competitor has reduced their prices recently."

    # Reasoning
    if churn_score == 1:
        reasoning = "Stable purchasing pattern, minimal price impact, and no complaints."
    elif churn_score == 2:
        reasoning = "Moderate churn risk due to noticeable price increase or minor service issues."
    else:
        reasoning = "High churn risk due to inactivity, major complaints, and strong competitor offers."

    question = f"{profile.strip()} Predict churn risk."
    answer = f"Churn Score: {churn_score}\nReasoning: {reasoning}\nAction: {ACTIONS[churn_score]}"

    # Format for OpenAI GPT-3.5 Turbo fine-tuning
    # OpenAI requires 'messages' format with role and content fields
    return {"messages": [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer}
    ]}


def generate_dataset(filename="churn_dataset_gpt35_turbo.jsonl", show_progress=True):
    counter = {1: 0, 2: 0, 3: 0}
    total = 0
    total_chars = 0
    max_chars_seen = 0
    
    with open(filename, "w", encoding="utf-8") as f:
        while total < TOTAL_RECORDS:
            for score in [1, 2, 3]:
                if counter[score] < TARGET_COUNTS[score]:
                    record = generate_customer_record(score)
                    
                    # Track character counts for OpenAI messages format
                    chars = sum(len(m['content']) for m in record['messages'])
                    
                    max_chars_seen = max(max_chars_seen, chars)
                    total_chars += chars
                    
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    counter[score] += 1
                    total += 1
                    if show_progress and total % 1000 == 0:
                        sys.stdout.write(f"\rProgress: {total}/{TOTAL_RECORDS}")
                        sys.stdout.flush()
                    if total >= TOTAL_RECORDS:
                        break
    
    avg_chars = total_chars / total
    avg_tokens = avg_chars / TOKEN_TO_CHAR_RATIO
    max_tokens = max_chars_seen / TOKEN_TO_CHAR_RATIO
    
    print(f"\n✅ Generated {TOTAL_RECORDS} records with distribution {counter}")
    print(f"📝 Format used: {OPENAI_FORMAT} (OpenAI messages format)")
    print(f"💾 Saved to: {filename}")
    print(f"\n📊 Token Analysis:")
    print(f"   Average chars per record: {avg_chars:.0f}")
    print(f"   Average tokens per record: {avg_tokens:.0f} (estimated)")
    print(f"   Max tokens in any record: {max_tokens:.0f} (estimated)")
    
    print(f"\n🔧 OpenAI GPT-3.5 Turbo Fine-tuning Settings:")
    print(f"   Model ID: gpt-3.5-turbo")
    print(f"   Format: {OPENAI_FORMAT} (required for chat models)")
    print(f"   Max Context Window: 4,096 tokens")
    
    print(f"\n📋 Fine-tuning Configuration:")
    print(f"   Epochs: OpenAI automatically determines (typically 1-4)")
    print(f"   Learning Rate: OpenAI manages automatically")
    print(f"   Batch Size: OpenAI manages automatically")
    print(f"   Max Token Count: Up to 4,096 tokens per training example")
    
    # Calculate recommendations based on 4096 token context limit
    if max_tokens > 4096:
        print(f"\n⚠️  WARNING: Some records exceed 4,096 token limit!")
        print(f"   Max tokens: {max_tokens:.0f} (limit: 4,096)")
        print(f"   Consider shortening prompts or reducing data per record")
    
    if avg_tokens <= 512:
        print(f"\n💡 Token Usage: Excellent (avg {avg_tokens:.0f} tokens/record)")
    elif avg_tokens <= 1024:
        print(f"\n💡 Token Usage: Good (avg {avg_tokens:.0f} tokens/record)")
    elif avg_tokens <= 2048:
        print(f"\n💡 Token Usage: Moderate (avg {avg_tokens:.0f} tokens/record)")
    else:
        print(f"\n💡 Token Usage: High (avg {avg_tokens:.0f} tokens/record)")
    
    print(f"\n💡 Notes:")
    print(f"   - GPT-3.5 Turbo is optimized for chat and text generation tasks")
    print(f"   - Fine-tune via OpenAI Fine-tuning API (https://platform.openai.com/docs/guides/fine-tuning)")
    print(f"   - Upload your JSONL file using: openai.File.create()")
    print(f"   - Create fine-tuning job using: openai.FineTuningJob.create()")
    print(f"   - Each training example must fit within 4,096 token context limit")
    print(f"   - OpenAI handles batch size, learning rate, and epochs automatically")

if __name__ == "__main__":
    generate_dataset()