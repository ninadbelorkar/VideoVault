import argparse
import sys
import os
import zipfile
import cv2
import numpy as np
import hashlib
import struct

try:
    import google.generativeai as genai
except ImportError:
    genai = None

CONTAINER_MAGIC_NUMBER = b'VVAULT_C'

APPEND_MAGIC_NUMBER = b'VVAULT' 

def get_ai_password():
    if not genai:
        return "Error: Gemini library not installed. Please run 'pip install google-generativeai'."
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY environment variable not set."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        prompt = "Generate a single, secure, 16-character password with uppercase, lowercase, numbers, and symbols. Provide only the password text and nothing else."
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: AI call failed. Details: {e}"

def get_ai_manifest(file_paths):
    if not genai:
        return "AI disabled. Please run 'pip install google-generativeai'."
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "AI disabled. GEMINI_API_KEY not set."
    
    content_to_summarize = ""
    for file_path in file_paths:
        if file_path.lower().endswith(('.txt', '.md', '.py', '.js', '.html', '.css')):
            try:
                with open(file_path, 'r', errors='ignore') as f:
                    content_to_summarize += f"--- Content from {os.path.basename(file_path)} ---\n"
                    content_to_summarize += f.read(2000) + "\n\n"
            except Exception:
                continue
    
    if not content_to_summarize:
        return "No text-based files found to summarize."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"""Summarize the following file content into a concise, one-sentence "manifest". Example: 'Contains Python scripts and project notes.'

Here is the content:
{content_to_summarize[:10000]}"""
        
        response = model.generate_content(prompt)
        return response.text.strip().replace('\n', ' ')
    except Exception as e:
        return f"Error: AI summarization failed. Details: {e}"

def peek_manifest_append(video_path):
    with open(video_path, 'rb') as f:
        data = f.read()
    magic_pos = data.rfind(CONTAINER_MAGIC_NUMBER)
    if magic_pos == -1:
        return "No manifest found (likely an older file format or not using the Append method)."
    
    header_start = magic_pos + len(CONTAINER_MAGIC_NUMBER)
    container_size = struct.unpack('>Q', data[header_start:header_start + 8])[0]
    container_data = data[header_start + 8 : header_start + 8 + container_size]
    
    temp_container_path = "peek_container.zip"
    with open(temp_container_path, 'wb') as f:
        f.write(container_data)
    try:
        with zipfile.ZipFile(temp_container_path, 'r') as zf:
            manifest = zf.read('manifest.txt').decode('utf-8')
            return manifest
    except Exception as e:
        return f"Could not read manifest: {e}"
    finally:
        if os.path.exists(temp_container_path):
            os.remove(temp_container_path)


def report_progress(percentage, message=""):
    """Prints progress to stdout so the Electron app can read it."""
    print(f"PROGRESS:{int(percentage)}:{message}")
    sys.stdout.flush()

def create_zip_archive(file_paths, temp_zip_path, password):
    """Creates a password-protected zip archive from a list of files."""

    with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        if password:
            zf.setpassword(password.encode('utf-8'))
        for i, file_path in enumerate(file_paths):
            zf.write(file_path, os.path.basename(file_path))

def encode_append(video_path, file_paths, output_path, password):
    """Appends a zipped archive (with AI manifest) to the end of a video file."""
    payload_zip_path = "payload.zip"
    container_zip_path = "container.zip"
    
    try:
        report_progress(5, "Generating AI manifest...")
        manifest_text = get_ai_manifest(file_paths)
        report_progress(10, f"AI Manifest: {manifest_text}")

        report_progress(15, "Zipping files...")
        create_zip_archive(file_paths, payload_zip_path, password)

        with zipfile.ZipFile(container_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(payload_zip_path, 'payload.zip')
            zf.writestr('manifest.txt', manifest_text)
        
        report_progress(20, "Container created. Appending to video...")
        
        with open(video_path, 'rb') as f_video, open(container_zip_path, 'rb') as f_zip:
            video_data = f_video.read()
            container_data = f_zip.read()

        header = CONTAINER_MAGIC_NUMBER + struct.pack('>Q', len(container_data))
        with open(output_path, 'wb') as f_out:
            f_out.write(video_data)
            f_out.write(header)
            f_out.write(container_data)
        
        report_progress(100, "Encoding complete with AI manifest!")

    finally:
        if os.path.exists(payload_zip_path): os.remove(payload_zip_path)
        if os.path.exists(container_zip_path): os.remove(container_zip_path)


def decode_append(video_path, output_dir, password):
    """Extracts an appended zip archive from a video file, handling manifest."""
    report_progress(0, "Searching for hidden data...")
    with open(video_path, 'rb') as f:
        data = f.read()

    magic_pos = data.rfind(CONTAINER_MAGIC_NUMBER)
    if magic_pos != -1:
        report_progress(10, "New format with manifest detected.")
        header_start = magic_pos + len(CONTAINER_MAGIC_NUMBER)
        container_size = struct.unpack('>Q', data[header_start:header_start + 8])[0]
        container_data = data[header_start + 8 : header_start + 8 + container_size]
        
        temp_container_path = "extracted_container.zip"
        with open(temp_container_path, 'wb') as f_zip:
            f_zip.write(container_data)
        
        try:
            with zipfile.ZipFile(temp_container_path, 'r') as container_zf:
                payload_data = container_zf.read('payload.zip')
                temp_payload_path = "extracted_payload.zip"
                with open(temp_payload_path, 'wb') as f_payload:
                    f_payload.write(payload_data)
                
                with zipfile.ZipFile(temp_payload_path, 'r') as payload_zf:
                    pwd = password.encode('utf-8') if password else None
                    payload_zf.extractall(path=output_dir, pwd=pwd)
                
                report_progress(100, f"Success! Files extracted to {output_dir}")
                os.remove(temp_payload_path)

        except Exception as e:
            report_progress(100, f"Error: Extraction failed. Incorrect password or corrupted data. Details: {e}")
        finally:
            if os.path.exists(temp_container_path):
                os.remove(temp_container_path)
    else:
        magic_pos = data.rfind(APPEND_MAGIC_NUMBER)
        if magic_pos == -1:
            report_progress(100, "Error: No hidden data found (magic number missing).")
            return
        
        report_progress(10, "Old format detected. No manifest available.")
        header_start = magic_pos + len(APPEND_MAGIC_NUMBER)
        zip_size = struct.unpack('>Q', data[header_start:header_start + 8])[0]
        zip_data = data[header_start + 8 : header_start + 8 + zip_size]
        temp_zip_path = "extracted_temp.zip"
        with open(temp_zip_path, 'wb') as f_zip:
            f_zip.write(zip_data)
        try:
            with zipfile.ZipFile(temp_zip_path, 'r') as zf:
                pwd = password.encode('utf-8') if password else None
                zf.extractall(path=output_dir, pwd=pwd)
            report_progress(100, f"Files successfully extracted to {output_dir}")
        except RuntimeError:
            report_progress(100, "Error: Extraction failed. Incorrect password or corrupted data.")
        finally:
            if os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)

def to_binary(data):
    """Convert data to a binary string."""
    return ''.join(format(byte, '08b') for byte in data)

def encode_steganography(video_path, file_paths, output_path, password):
    temp_zip_path = "temp_archive.zip"
    try:
        create_zip_archive(file_paths, temp_zip_path, password)
        with open(temp_zip_path, 'rb') as f:
            data_to_hide = f.read()
        data_size = len(data_to_hide)
        header = struct.pack('>Q', data_size)
        binary_data = to_binary(header + data_to_hide)
        data_len = len(binary_data)
        report_progress(10, "Data prepared for embedding.")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            report_progress(100, "Error: Could not open video file.")
            return
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        fourcc = cv2.VideoWriter_fourcc(*'FFV1')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        total_pixels = width * height * 3
        max_capacity = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) * total_pixels
        if data_len > max_capacity:
            report_progress(100, f"Error: Data size ({data_len} bits) exceeds video capacity ({max_capacity} bits).")
            return
        data_idx = 0
        frame_idx = 0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            if data_idx < data_len:
                frame_flat = frame.flatten()
                for i in range(len(frame_flat)):
                    if data_idx < data_len:
                        pixel_val = frame_flat[i]
                        bit_to_hide = int(binary_data[data_idx])
                        frame_flat[i] = (pixel_val & 0b11111110) | bit_to_hide
                        data_idx += 1
                    else: break
                frame = frame_flat.reshape(frame.shape)
            out.write(frame)
            frame_idx += 1
            if total_frames > 0:
                progress = 10 + (frame_idx / total_frames * 90)
                report_progress(progress, f"Processing frame {frame_idx}/{total_frames}")
        cap.release()
        out.release()
        report_progress(100, "Steganography encoding complete.")
    finally:
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)

def decode_steganography(video_path, output_dir, password):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        report_progress(100, "Error: Could not open video file.")
        return
    report_progress(5, "Reading video frames...")
    binary_data = ""
    header_len = 64
    data_size = None
    frame_idx = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    while cap.isOpened() and (data_size is None or len(binary_data) < header_len + data_size * 8):
        ret, frame = cap.read()
        if not ret: break
        frame_flat = frame.flatten()
        for pixel_val in frame_flat:
            binary_data += str(pixel_val & 1)
            if data_size is None and len(binary_data) == header_len:
                header_bytes = int(binary_data, 2).to_bytes(header_len // 8, byteorder='big')
                data_size = struct.unpack('>Q', header_bytes)[0]
                report_progress(15, f"Header decoded. Expecting {data_size} bytes.")
            if data_size is not None and len(binary_data) >= header_len + data_size * 8: break
        if data_size is not None and len(binary_data) >= header_len + data_size * 8: break
        frame_idx += 1
        if total_frames > 0:
            progress = 15 + (frame_idx / total_frames * 75)
            report_progress(progress, f"Scanning frame {frame_idx}/{total_frames}")
    cap.release()
    if data_size is None:
        report_progress(100, "Error: Could not decode header. No hidden data found or data is corrupt.")
        return
    if data_size > 0:
        payload_binary = binary_data[header_len : header_len + data_size * 8]
        if len(payload_binary) < data_size * 8:
             report_progress(100, "Error: Data is corrupted or incomplete.")
             return
        payload_bytes = int(payload_binary, 2).to_bytes(data_size, byteorder='big')
    else:
        payload_bytes = b''
    report_progress(90, "Data extracted. Unzipping...")
    temp_zip_path = "extracted_temp.zip"
    with open(temp_zip_path, 'wb') as f:
        f.write(payload_bytes)
    try:
        with zipfile.ZipFile(temp_zip_path, 'r') as zf:
            if not zf.namelist():
                report_progress(100, "Success: Decoded video, but it contained no hidden files.")
                return
            pwd = password.encode('utf-8') if password else None
            try:
                zf.extractall(path=output_dir, pwd=pwd)
                num_files = len(zf.namelist())
                report_progress(100, f"Success! {num_files} file(s) extracted to {output_dir}")
            except RuntimeError as e:
                if 'password' in str(e):
                    report_progress(100, "Error: Extraction failed. The password is likely incorrect.")
                else:
                    report_progress(100, f"Error: A runtime error occurred during extraction: {e}")
    except zipfile.BadZipFile:
        report_progress(100, "Error: Failed to decode. The data in the video is not a valid archive or is corrupted.")
    except Exception as e:
        report_progress(100, f"An unexpected error occurred: {e}")
    finally:
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)

def encode_datareel(file_paths, output_path, password):
    frame_width, frame_height = 640, 360
    pixels_per_frame = frame_width * frame_height
    fps = 30
    temp_zip_path = "temp_archive.zip"
    try:
        create_zip_archive(file_paths, temp_zip_path, password)
        with open(temp_zip_path, 'rb') as f:
            data_to_hide = f.read()
        magic = b'VREEL'
        checksum = hashlib.sha256(data_to_hide).digest()
        data_size_bytes = struct.pack('>Q', len(data_to_hide))
        header = magic + checksum + data_size_bytes
        binary_data = to_binary(header + data_to_hide)
        data_len = len(binary_data)
        report_progress(20, "Data prepared. Generating video frames...")
        fourcc = cv2.VideoWriter_fourcc(*'FFV1')
        out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height), isColor=False)
        num_frames = (data_len + pixels_per_frame - 1) // pixels_per_frame
        for i in range(num_frames):
            start = i * pixels_per_frame
            end = start + pixels_per_frame
            chunk = binary_data[start:end].ljust(pixels_per_frame, '0')
            pixel_values = np.array([255 if bit == '1' else 0 for bit in chunk], dtype=np.uint8)
            frame = pixel_values.reshape((frame_height, frame_width))
            out.write(frame)
            if total_frames > 0:
                progress = 20 + (i / num_frames * 80)
                report_progress(progress, f"Writing frame {i+1}/{num_frames}")
        out.release()
        report_progress(100, "Data-Reel video created successfully.")
    finally:
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)

def decode_datareel(video_path, output_dir, password):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        report_progress(100, "Error: Could not open video file.")
        return
    report_progress(5, "Reading Data-Reel video...")
    binary_data = ""
    frame_idx = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        if len(frame.shape) == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh_frame = cv2.threshold(frame, 127, 255, cv2.THRESH_BINARY)
        for row in thresh_frame:
            for pixel in row:
                binary_data += '1' if pixel == 255 else '0'
        frame_idx += 1
        if total_frames > 0:
            progress = 5 + (frame_idx / total_frames * 75)
            report_progress(progress, f"Reading frame {frame_idx}/{total_frames}")
    cap.release()
    report_progress(80, "Video read. Parsing data header...")
    header_offset = 0
    magic = int(binary_data[:40], 2).to_bytes(5, byteorder='big')
    if magic != b'VREEL':
        report_progress(100, "Error: Not a valid Data-Reel file (magic number mismatch).")
        return
    header_offset += 40
    checksum_bin = binary_data[header_offset : header_offset + 256]
    checksum = int(checksum_bin, 2).to_bytes(32, byteorder='big')
    header_offset += 256
    data_size_bin = binary_data[header_offset : header_offset + 64]
    data_size = int(data_size_bin, 2)
    header_offset += 64
    report_progress(85, f"Header decoded. Expecting {data_size} bytes.")
    payload_binary = binary_data[header_offset : header_offset + data_size * 8]
    payload_bytes = int(payload_binary, 2).to_bytes(data_size, byteorder='big')
    if hashlib.sha256(payload_bytes).digest() != checksum:
        report_progress(100, "Error: Checksum mismatch. Data is corrupted.")
        return
    report_progress(90, "Checksum OK. Extracting archive...")
    temp_zip_path = "extracted_temp.zip"
    with open(temp_zip_path, 'wb') as f:
        f.write(payload_bytes)
    try:
        with zipfile.ZipFile(temp_zip_path, 'r') as zf:
            pwd = password.encode('utf-8') if password else None
            zf.extractall(path=output_dir, pwd=pwd)
        report_progress(100, f"Files successfully extracted to {output_dir}")
    except RuntimeError:
        report_progress(100, "Error: Extraction failed. Incorrect password or corrupted data.")
    finally:
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="VideoVault Backend Engine")
    parser.add_argument('--method', choices=['append', 'steganography', 'datareel'])
    parser.add_argument('--mode', required=True, choices=['encode', 'decode', 'ai'])
    parser.add_argument('--password', help="Password for the archive.")
    parser.add_argument('--output', help="Path for the output file or folder.")
    parser.add_argument('inputs', nargs='*', help="Input file paths.")
    parser.add_argument('--ai-task', choices=['password', 'peek'], help="The specific AI task to run.")
    args = parser.parse_args()

    if args.mode == 'ai':
        if args.ai_task == 'password':
            print(f"AI_RESULT:{get_ai_password()}")
        elif args.ai_task == 'peek':
            if not args.inputs:
                print("ERROR: Peek requires an input video file.", file=sys.stderr)
                sys.exit(1)
            print(f"AI_RESULT:{peek_manifest_append(args.inputs[0])}")

    elif args.mode == 'encode':
        if not args.inputs:
            print("ERROR: Encoding requires at least one input file.", file=sys.stderr)
            sys.exit(1)
        if not args.output:
            print("ERROR: Encoding requires an output path.", file=sys.stderr)
            sys.exit(1)
        if args.method == 'append':
            encode_append(args.inputs[0], args.inputs[1:], args.output, args.password)
        elif args.method == 'steganography':
            encode_steganography(args.inputs[0], args.inputs[1:], args.output, args.password)
        elif args.method == 'datareel':
            encode_datareel(args.inputs, args.output, args.password)

    elif args.mode == 'decode':
        if not args.inputs or len(args.inputs) != 1:
            print("ERROR: Decoding requires exactly one input video file.", file=sys.stderr)
            sys.exit(1)
        if not args.output:
            print("ERROR: Decoding requires an output path.", file=sys.stderr)
            sys.exit(1)
        video_to_decode = args.inputs[0]
        if args.method == 'append':
            decode_append(video_to_decode, args.output, args.password)
        elif args.method == 'steganography':
            decode_steganography(video_to_decode, args.output, args.password)
        elif args.method == 'datareel':
            decode_datareel(video_to_decode, args.output, args.password)