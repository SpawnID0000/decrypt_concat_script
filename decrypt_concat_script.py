import os
import subprocess

# Input file for splitting & encrypting

file_name_no_ext = "ba7be4d0-e73f-4ecc-94d9-6658b510c69b_7c0ecbde-84d4-48c7-8cf4-77cecce423af"  # Replace with actual file name (artistMBID_recordingMBID)
file_name_ext = ".mp3"                                                                          # Replace with actual file extension
file_name = file_name_no_ext + file_name_ext
file_name_part_ = file_name + "_part_"
file_path = os.path.join(os.getcwd(), file_name)

directory = os.path.dirname(file_path)
gpg_path = "/usr/local/bin/gpg"  # Replace with your actual path to gpg
os.environ["PATH"] += os.pathsep + "/usr/local/bin"

# Decrypt file
for file in os.listdir(directory):
    if file.startswith(os.path.basename(file_name_part_)) and file.endswith('.gpg'):
        full_path = os.path.join(directory, file)
        decrypted_file_path = full_path.rstrip('.gpg')
        
        # Decryption command
        result = subprocess.run([gpg_path, "-d", "--output", decrypted_file_path, "--batch", "--yes", "--passphrase", file_name_no_ext, full_path])
        
        # Check if decryption was successful
        if result.returncode != 0:
            print(f"Failed to decrypt {full_path}.")
            continue

# Concatenate file chunks to reassemble original file
output_file = os.path.join(directory, file_name_no_ext + file_name_ext)
with open(output_file, 'wb') as fout:
    for file in sorted(os.listdir(directory)):
        if file.startswith(os.path.basename(file_name_part_)) and not file.endswith('.gpg'):
            with open(os.path.join(directory, file), 'rb') as fin:
                fout.write(fin.read())

# Cleanup: Delete both encrypted and decrypted file chunks
for file in os.listdir(directory):
    if file.startswith(os.path.basename(file_name_part_)):
        os.remove(os.path.join(directory, file))

print("Decryption, reassembly, and cleanup complete!")