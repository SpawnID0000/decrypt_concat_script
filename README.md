# decrypt_concat_script
Unzips package of encrypted file chunks then decrypts & concatenates to recover the original file

_Note: For use with split_encrypt_script (https://github.com/SpawnID0000/split_encrypt_script)_

Before running this script, install or upgrade Python's cryptography module if not already running the latest:

     pip show cryptography

     pip install --upgrade cryptography

Additional usage notes:

- Executing the script requires the following command line format:

        python3 decrypt_concat_script.py path/to/encrypted path/to/output

- Run the script with working directory set to the same location as the script

- 'path/to/encryted' is the directory where the target zip files are stored
     - Include the full path (e.g. using drag & drop)
     - Do not include file in the path (i.e. directory only)
 
- 'path/to/output' is the directory where the output files should be saved
     - Again, include the full path
