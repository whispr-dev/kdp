import os

def convert_txt_to_md(directory):
    count = 0
    for filename in os.listdir(directory):
        if filename.lower().endswith(".txt"):
            txt_path = os.path.join(directory, filename)
            md_filename = os.path.splitext(filename)[0] + ".md"
            md_path = os.path.join(directory, md_filename)

            with open(txt_path, "r", encoding="utf-8") as f_in:
                content = f_in.read()

            with open(md_path, "w", encoding="utf-8") as f_out:
                f_out.write(content)

            print(f"✅ Converted: {filename} → {md_filename}")
            count += 1

    if count == 0:
        print("ℹ️ No .txt files found in the specified folder.")
    else:
        print(f"\n🎉 Finished converting {count} file(s)!")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        target_dir = os.getcwd()

    if not os.path.isdir(target_dir):
        print("❌ Error: Provided path is not a valid folder.")
    else:
        convert_txt_to_md(target_dir)
