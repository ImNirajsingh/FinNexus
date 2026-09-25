from description_features import extract_transaction_features


test_descriptions = [
    "UPI/Akhilesh Yadav/690842000757/Pay to BharatPe",
    "UPI/RAUSHAN RAJ/535788035697/Pay to BharatPe",
    "UPI/Mr NARESH KUMAR/398146553121/Pay to BharatPe",
    "UPI/Ayush Gupta/865470506987/Payment from Ph",
]


for description in test_descriptions:

    print("=" * 70)
    print("DESCRIPTION:")
    print(description)

    result = extract_transaction_features(description)

    print("\nEXTRACTED FEATURES:")

    for key, value in result.items():
        print(f"{key:20}: {value}")