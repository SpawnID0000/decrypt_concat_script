# decrypt_concat_script
Unzips package of encrypted file chunks then decrypts & concatenates to recover the original file

_Note: For use with split_encrypt_script (https://github.com/SpawnID0000/split_encrypt_script)_

Before running this script, install or upgrade Python's cryptography module if not already running the latest:

     pip show cryptography

     pip install --upgrade cryptography

Run the script using the following command line format:

     python3 decrypt_concat_script.py [-h] [--log] input_path [output_dir]
