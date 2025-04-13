import os

def save_to_file(category_id, data):
    try:
        os.makedirs('app/output', exist_ok=True)
        file_path = f"app/output/{category_id}.txt"

        with open(file_path, "w") as f:
            f.write(f"Text: {data['text']}\n")
            f.write(f"Category: {data['category']}\n")
            f.write(f"Remarks: {data['remarks']}\n")
            f.write(f"Description: {data['description']}\n\n")
    except Exception as e:
        raise Exception(f"Error saving file: {e}")
