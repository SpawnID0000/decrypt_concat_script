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

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.backends import default_backend
except ImportError:
    print("The cryptography module is not installed. Please install it using 'pip install cryptography'")
    exit(1)

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

def process_package(package_info):
    path, input_root, output_root, is_zip = package_info
    extracted_dir = os.path.join(os.path.dirname(path), Path(path).stem) if is_zip else path

    try:
        if is_zip:
            os.makedirs(extracted_dir, exist_ok=True)
            with zipfile.ZipFile(path, 'r') as zip_ref:
                for zip_info in zip_ref.infolist():
                    if zip_info.filename.endswith('/'):  # Skip directories
                        continue
                    zip_info.filename = os.path.basename(zip_info.filename)
                    zip_ref.extract(zip_info, extracted_dir)

        decrypted_files = {}
        for aes_file in sorted(os.listdir(extracted_dir)):
            if aes_file.endswith('.aes'):
                full_path = os.path.join(extracted_dir, aes_file)
                parts = Path(aes_file).stem.split('_')
                passphrase = '_'.join(parts[:-2])
                original_ext = '.' + aes_file.rsplit('.', 2)[-2] if '.' in aes_file else ''

                with open(full_path, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = aes_decrypt(encrypted_data, passphrase)

                if passphrase not in decrypted_files:
                    decrypted_files[passphrase] = b''
                decrypted_files[passphrase] += decrypted_data

                os.remove(full_path)

        for passphrase, data in decrypted_files.items():
            output_file_path = Path(output_root, f"{passphrase}{original_ext}")
            os.makedirs(output_file_path.parent, exist_ok=True)

            with open(output_file_path, 'wb') as fout:
                fout.write(data)

        if not os.listdir(extracted_dir):
            os.rmdir(extracted_dir)

        return f"Processed package or folder: {path}"

    except Exception as e:
        return f"Error processing package or folder {path}: {e}"

def process_directory_or_file(input_path, output_dir):
    items_to_process = []
    if os.path.isdir(input_path):
        for root, dirs, files in os.walk(input_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]  # Skip hidden directories
            for file in files:
                if file.endswith('.zip') and not file.startswith('._'):
                    items_to_process.append((os.path.join(root, file), input_path, output_dir, True))
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                items_to_process.append((dir_path, input_path, output_dir, False))
    elif os.path.isfile(input_path) and input_path.endswith('.zip'):
        items_to_process.append((input_path, os.path.dirname(input_path), output_dir, True))
    else:
        raise ValueError("Input path must be a directory or a .zip file")

    with Pool() as pool:
        return pool.map(process_package, items_to_process)

def resolve_path(path):
    """Resolve the given path to an absolute path."""
    return os.path.abspath(path)

def main():
    parser = argparse.ArgumentParser(description='Decrypt and concatenate audio files.')
    parser.add_argument('input_path', type=str, help='Directory name or path to the directory or zip file with encrypted files')
    parser.add_argument('output_dir', type=str, nargs='?', default=os.getcwd(),
                        help='Directory name or path to the output directory (optional, defaults to current working directory)')
    parser.add_argument('--log', action='store_true', help='Enable logging to a file (optional, disabled by default)')
    args = parser.parse_args()

    if args.log:
        script_name = os.path.splitext(os.path.basename(__file__))[0]
        log_file = f"{script_name}_log.txt"
        logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    input_path = resolve_path(args.input_path)
    output_dir = resolve_path(args.output_dir)

    print(f"Processing items from {input_path}... Output will be saved to {output_dir}")
    start_time = time.time()

    try:
        results = process_directory_or_file(input_path, output_dir)
        for result in results:
            if args.log:
                logging.info(result)
            print(result)
    except ValueError as e:
        if args.log:
            logging.error(str(e))
        print(str(e))

    total_duration = time.time() - start_time
    if args.log:
        logging.info(f"Total script execution duration: {total_duration:.2f} seconds")
    print("Decryption and concatenation complete!")

if __name__ == "__main__":
    main()
