import os
import argparse
import zipfile
import logging
import time
from multiprocessing import Pool
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from pathlib import Path

# AES decryption function
def aes_decrypt(encrypted_data, passphrase):
    backend = default_backend()
    key = passphrase.ljust(32)[:32].encode()
    iv = encrypted_data[:16]
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=backend)
    decryptor = cipher.decryptor()

    unpadder = padding.PKCS7(128).unpadder()
    decrypted_padded_data = decryptor.update(encrypted_data[16:]) + decryptor.finalize()
    decrypted_data = unpadder.update(decrypted_padded_data) + unpadder.finalize()

    return decrypted_data

# Function to process a single ZIP package
def process_zip_package(zip_info):
    zip_path, input_root, output_root = zip_info
    extracted_dir = os.path.join(os.path.dirname(zip_path), Path(zip_path).stem)

    try:
        os.makedirs(extracted_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extract files directly into extracted_dir, ignoring any internal directory structure
            for zip_info in zip_ref.infolist():
                if zip_info.filename.endswith('/'):  # Skip directories
                    continue
                zip_info.filename = os.path.basename(zip_info.filename)  # Extract only the file, not the full path
                zip_ref.extract(zip_info, extracted_dir)

        decrypted_files = {}
        for aes_file in sorted(os.listdir(extracted_dir)):
            if aes_file.endswith('.aes'):
                full_path = os.path.join(extracted_dir, aes_file)
                parts = Path(aes_file).stem.split('_')
                passphrase = '_'.join(parts[:-2])  # Remove '_part_xx' and '.ext'
                original_ext = '.' + aes_file.split('.')[-2]  # Get the original extension

                with open(full_path, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = aes_decrypt(encrypted_data, passphrase)

                if passphrase not in decrypted_files:
                    decrypted_files[passphrase] = b''
                decrypted_files[passphrase] += decrypted_data

                os.remove(full_path)

        for passphrase, data in decrypted_files.items():
            relative_dir = Path(zip_path).parent.relative_to(input_root)
            output_dir = Path(output_root, relative_dir)
            os.makedirs(output_dir, exist_ok=True)

            output_file_path = output_dir / f"{passphrase}{original_ext}"
            with open(output_file_path, 'wb') as fout:
                fout.write(data)

        os.rmdir(extracted_dir)
        return f"Processed ZIP package: {zip_path}"

    except Exception as e:
        return f"Error processing package {zip_path}: {e}"



def main():
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    log_file = f"{script_name}_log.txt"
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    start_time = time.time()

    parser = argparse.ArgumentParser(description='Decrypt and concatenate audio files. \n\nUsage: python3 decrypt_concat_script.py path/to/encrypted path/to/output',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('input_dir', type=str, help='Path to the directory with encrypted files')
    parser.add_argument('output_dir', type=str, help='Path to the output directory')
    args = parser.parse_args()

    zip_packages_to_process = []
    for root, dirs, files in os.walk(args.input_dir):
        for file in files:
            if file.endswith('.zip'):
                zip_packages_to_process.append((os.path.join(root, file), args.input_dir, args.output_dir))

    print("Processing ZIP packages...")
    with Pool() as pool:
        results = pool.map(process_zip_package, zip_packages_to_process)

    # Logging results
    for result in results:
        logging.info(result)  # Comment out or remove this line to suppress detailed logging
        print(result)

    total_duration = time.time() - start_time
    logging.info(f"Total script execution duration: {total_duration:.2f} seconds")
    print("Decryption and concatenation complete!")

if __name__ == "__main__":
    main()
