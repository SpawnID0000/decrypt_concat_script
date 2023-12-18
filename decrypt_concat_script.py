import os
import subprocess
import argparse
import zipfile
import logging
import time
from pathlib import Path

# Initialize logging
script_name = os.path.splitext(os.path.basename(__file__))[0]
log_file = f"{script_name}_log.txt"
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Start time for duration calculation
start_time = time.time()

# Parse command line arguments
parser = argparse.ArgumentParser(description='Decrypt and concatenate audio files. \n\nUsage: python3 decrypt_concat_script.py path/to/encrypted path/to/output',
                                 formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('input_dir', type=str, help='Path to the directory with encrypted files')
parser.add_argument('output_dir', type=str, help='Path to the output directory')
args = parser.parse_args()

# Decrypt and concatenate function
def decrypt_and_concatenate(input_dir, output_dir):
    file_count = 0
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.startswith('.') or not file.endswith('.zip'):  # Skip hidden files and non-ZIP files
                continue

            try:
                # Unzip the package
                zip_path = os.path.join(root, file)
                print(f"Extracting ZIP package: {zip_path}")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(root)

                # Process the unzipped files
                extracted_files = [filename for filename in os.listdir(root) if filename.endswith('.gpg')]
                for part_file in extracted_files:
                    full_path = os.path.join(root, part_file)
                    passphrase = os.path.basename(part_file).split('_part_')[0]
                    decrypted_file_path = full_path.rstrip('.gpg')

                    # Define the output file path, preserving the directory structure
                    relative_dir = os.path.relpath(root, input_dir)
                    output_subdir = os.path.join(output_dir, relative_dir)
                    os.makedirs(output_subdir, exist_ok=True)
                    output_file_path = os.path.join(output_subdir, passphrase + ".opus")  # Default to '.opus'

                    # Decrypt file
                    gpg_path = "/usr/local/bin/gpg"
                    print(f"Decrypting file: {part_file} using passphrase: {passphrase}")
                    subprocess.run([gpg_path, "-d", "--output", decrypted_file_path, "--batch", "--yes", "--passphrase", passphrase, full_path])

                    # Concatenate file
                    with open(output_file_path, 'ab') as fout:
                        with open(decrypted_file_path, 'rb') as fin:
                            fout.write(fin.read())

                    # Cleanup decrypted chunk
                    os.remove(decrypted_file_path)

                # Delete the unzipped .gpg files after processing
                for part_file in extracted_files:
                    os.remove(os.path.join(root, part_file))

                file_count += 1
                print(f"Processed ZIP package: {zip_path}")
                #logging.info(f"Processed ZIP package: {zip_path}")

            except Exception as e:
                logging.error(f"Error processing package {zip_path}: {e}")

    return file_count

# Running the function and logging results
file_count = decrypt_and_concatenate(args.input_dir, args.output_dir)
total_duration = time.time() - start_time
logging.info(f"Total files processed: {file_count}")
logging.info(f"Total script execution duration: {total_duration:.2f} seconds")
print("Decryption and concatenation complete!")
