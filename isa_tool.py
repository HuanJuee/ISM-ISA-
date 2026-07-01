#!/usr/bin/env python3
"""
ISA Archive Tool for "sisters~夏の最後の日~"
ISA archive tool for ISM engine games.
"""

import struct
import os
import sys
import argparse

# ISA file header signature
ISA_HEADER = b'ISM ENGLISH '
HEADER_SIZE = 12
FILE_COUNT_SIZE = 4
ENTRY_SIZE = 64

# Offsets within file entry
FILENAME_OFFSET = 0
FILENAME_SIZE = 32
RESERVED1_SIZE = 16
UNKNOWN1_OFFSET = FILENAME_SIZE + RESERVED1_SIZE
UNKNOWN1_SIZE = 4
DATA_OFFSET_OFFSET = UNKNOWN1_OFFSET + UNKNOWN1_SIZE
DATA_OFFSET_SIZE = 4
FILE_SIZE_OFFSET = DATA_OFFSET_OFFSET + DATA_OFFSET_SIZE
FILE_SIZE_SIZE = 4
UNKNOWN2_OFFSET = FILE_SIZE_OFFSET + FILE_SIZE_SIZE
UNKNOWN2_SIZE = 4

# Filename encodings (Japanese games use Shift-JIS)
FILENAME_ENCODINGS = ['shift_jis', 'cp932', 'shift_jisx0213']


def decode_filename(filename_bytes):
    """Decode filename bytes, trying multiple encodings."""
    # Strip trailing null bytes
    data = filename_bytes.split(b'\x00')[0]
    if not data:
        return ''
    
    # Try encodings in priority order
    for encoding in FILENAME_ENCODINGS:
        try:
            return data.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    
    # All failed, use replace mode
    return data.decode('shift_jis', errors='replace')


def encode_filename(filename):
    """Encode filename string to Shift-JIS bytes."""
    encoded = filename.encode('shift_jis')
    if len(encoded) > FILENAME_SIZE - 1:
        raise ValueError(f"Filename too long (>{FILENAME_SIZE - 1} bytes after encoding): {filename}")
    return encoded


def read_isa_entries(file_path):
    """Read all file entries from ISA file."""
    with open(file_path, 'rb') as f:
        # Read header
        header = f.read(HEADER_SIZE)
        if header != ISA_HEADER:
            raise ValueError(f"Invalid ISA header: {header}")
        
        # Read file count
        file_count = struct.unpack('<I', f.read(FILE_COUNT_SIZE))[0]
        
        entries = []
        for i in range(file_count):
            entry_start = HEADER_SIZE + FILE_COUNT_SIZE + i * ENTRY_SIZE
            f.seek(entry_start)
            
            # Read filename
            filename_data = f.read(FILENAME_SIZE)
            filename = decode_filename(filename_data)
            
            # Skip reserved area
            f.read(RESERVED1_SIZE)
            
            # Read unknown1
            unknown1 = struct.unpack('<I', f.read(UNKNOWN1_SIZE))[0]
            
            # Read data offset
            data_offset = struct.unpack('<I', f.read(DATA_OFFSET_SIZE))[0]
            
            # Read file size
            file_size = struct.unpack('<I', f.read(FILE_SIZE_SIZE))[0]
            
            # Read unknown2
            unknown2 = struct.unpack('<I', f.read(UNKNOWN2_SIZE))[0]
            
            entries.append({
                'filename': filename,
                'unknown1': unknown1,
                'unknown2': unknown2,
                'data_offset': data_offset,
                'file_size': file_size
            })
        
        return entries


def extract_isa(file_path, output_dir):
    """Extract all files from ISA archive to directory."""
    entries = read_isa_entries(file_path)
    
    os.makedirs(output_dir, exist_ok=True)
    
    with open(file_path, 'rb') as f:
        for entry in entries:
            f.seek(entry['data_offset'])
            data = f.read(entry['file_size'])
            
            output_path = os.path.join(output_dir, entry['filename'])
            with open(output_path, 'wb') as out_f:
                out_f.write(data)
            
            print(f"  Extract: {entry['filename']} ({entry['file_size']} bytes)")
    
    print(f"\nDone! Extracted {len(entries)} files to {output_dir}")


def create_isa(input_dir, output_path):
    """Create ISA archive from directory."""
    # Get all files in directory
    files = []
    for filename in sorted(os.listdir(input_dir)):
        filepath = os.path.join(input_dir, filename)
        if os.path.isfile(filepath):
            files.append(filename)
    
    if not files:
        print("Error: No files in directory")
        return
    
    print(f"Found {len(files)} files, creating archive...")
    
    # Calculate directory size
    dir_size = HEADER_SIZE + FILE_COUNT_SIZE + len(files) * ENTRY_SIZE
    
    # Calculate data offsets (starting after directory)
    current_offset = dir_size
    
    entries = []
    file_data_list = []
    
    for filename in files:
        filepath = os.path.join(input_dir, filename)
        with open(filepath, 'rb') as f:
            data = f.read()
        
        file_size = len(data)
        
        entries.append({
            'filename': filename,
            'unknown1': 0,
            'unknown2': 0,
            'data_offset': current_offset,
            'file_size': file_size
        })
        
        file_data_list.append(data)
        current_offset += file_size
        
        print(f"  Add: {filename} ({file_size} bytes)")
    
    # Write ISA file
    with open(output_path, 'wb') as f:
        # Write header
        f.write(ISA_HEADER)
        
        # Write file count
        f.write(struct.pack('<I', len(files)))
        
        # Write file entries
        for entry in entries:
            # Filename (32 bytes, null-padded)
            filename_bytes = encode_filename(entry['filename'])
            f.write(filename_bytes)
            f.write(b'\x00' * (FILENAME_SIZE - len(filename_bytes)))
            
            # Reserved area (16 bytes, all zeros)
            f.write(b'\x00' * RESERVED1_SIZE)
            
            # unknown1
            f.write(struct.pack('<I', entry['unknown1']))
            
            # data offset
            f.write(struct.pack('<I', entry['data_offset']))
            
            # file size
            f.write(struct.pack('<I', entry['file_size']))
            
            # unknown2
            f.write(struct.pack('<I', entry['unknown2']))
        
        # Write file data
        for data in file_data_list:
            f.write(data)
    
    print(f"\nDone! Created {output_path}")
    print(f"Total size: {os.path.getsize(output_path)} bytes")


def list_isa(file_path):
    """List all files in ISA archive."""
    entries = read_isa_entries(file_path)
    
    print(f"ISA file: {file_path}")
    print(f"File count: {len(entries)}")
    print()
    print(f"{'Filename':<40} {'Size':>10} {'Offset':>12}")
    print("-" * 67)
    
    total_size = 0
    for entry in entries:
        print(f"{entry['filename']:<40} {entry['file_size']:>10} 0x{entry['data_offset']:08X}")
        total_size += entry['file_size']
    
    print("-" * 67)
    print(f"{'Total':<40} {total_size:>10}")


def replace_file_in_isa(isa_path, filename_in_isa, new_file_path):
    """Replace a single file in ISA archive."""
    entries = read_isa_entries(isa_path)
    
    # Find target file
    target_entry = None
    target_index = -1
    for i, entry in enumerate(entries):
        if entry['filename'].lower() == filename_in_isa.lower():
            target_entry = entry
            target_index = i
            break
    
    if target_entry is None:
        print(f"Error: File '{filename_in_isa}' not found in ISA archive")
        return False
    
    # Read new file content
    with open(new_file_path, 'rb') as f:
        new_data = f.read()
    
    new_size = len(new_data)
    old_size = target_entry['file_size']
    
    print(f"Replacing: {filename_in_isa}")
    print(f"  Old size: {old_size} bytes")
    print(f"  New size: {new_size} bytes")
    
    # Read entire ISA file
    with open(isa_path, 'rb') as f:
        isa_data = f.read()
    
    if new_size <= old_size:
        # New file is smaller or equal, can replace in-place
        print("  New file is smaller, replacing in-place")
        
        # Replace data
        offset = target_entry['data_offset']
        new_isa_data = bytearray(isa_data)
        new_isa_data[offset:offset+new_size] = new_data
        
        # If new file is smaller, pad with zeros
        if new_size < old_size:
            new_isa_data[offset+new_size:offset+old_size] = b'\x00' * (old_size - new_size)
        
        # Update file size in directory (offset stays the same)
        entry_offset = 16 + target_index * 64 + 56  # 56 is offset of size field in entry
        struct.pack_into('<I', new_isa_data, entry_offset, new_size)
        
        # Write back
        with open(isa_path, 'wb') as f:
            f.write(new_isa_data)
        
        print("  Replace complete!")
        return True
    else:
        # New file is larger, need to re-layout
        print("  New file is larger, re-laying out files...")
        
        # Read all file data
        file_datas = {}
        with open(isa_path, 'rb') as f:
            for entry in entries:
                f.seek(entry['data_offset'])
                file_datas[entry['filename']] = f.read(entry['file_size'])
        
        # Replace target file
        file_datas[filename_in_isa] = new_data
        
        # Recalculate offsets (maintaining original directory order)
        dir_size = 16 + len(entries) * 64
        current_offset = dir_size
        
        new_entries = []
        for entry in entries:
            data = file_datas[entry['filename']]
            new_entries.append({
                'filename': entry['filename'],
                'unknown1': entry['unknown1'],
                'unknown2': entry['unknown2'],
                'data_offset': current_offset,
                'file_size': len(data)
            })
            current_offset += len(data)
        
        # Write new ISA file
        with open(isa_path, 'wb') as f:
            # Write header
            f.write(ISA_HEADER)
            f.write(struct.pack('<I', len(entries)))
            
            # Write file entries
            for entry in new_entries:
                filename_bytes = encode_filename(entry['filename'])
                f.write(filename_bytes)
                f.write(b'\x00' * (32 - len(filename_bytes)))
                f.write(b'\x00' * 16)  # reserved
                f.write(struct.pack('<I', entry['unknown1']))
                f.write(struct.pack('<I', entry['data_offset']))
                f.write(struct.pack('<I', entry['file_size']))
                f.write(struct.pack('<I', entry['unknown2']))
            
            # Write file data
            for entry in entries:
                f.write(file_datas[entry['filename']])
        
        print("  Replace complete!")
        return True


def extract_single_file(isa_path, filename_in_isa, output_path):
    """Extract a single file from ISA archive."""
    entries = read_isa_entries(isa_path)
    
    # Find file
    target_entry = None
    for entry in entries:
        if entry['filename'].lower() == filename_in_isa.lower():
            target_entry = entry
            break
    
    if target_entry is None:
        print(f"Error: File '{filename_in_isa}' not found in ISA archive")
        return False
    
    # Read file data
    with open(isa_path, 'rb') as f:
        f.seek(target_entry['data_offset'])
        data = f.read(target_entry['file_size'])
    
    # Write output file
    with open(output_path, 'wb') as f:
        f.write(data)
    
    print(f"Extracted: {filename_in_isa} -> {output_path} ({len(data)} bytes)")
    return True


def main():
    parser = argparse.ArgumentParser(description='ISA Archive Tool - ISM engine ISA archive utility')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract ISA archive to directory')
    extract_parser.add_argument('isa_file', help='ISA file path')
    extract_parser.add_argument('-o', '--output', default='extracted', help='Output directory (default: extracted)')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create ISA archive from directory')
    create_parser.add_argument('input_dir', help='Input directory')
    create_parser.add_argument('-o', '--output', default='output.isa', help='Output ISA file (default: output.isa)')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List files in ISA archive')
    list_parser.add_argument('isa_file', help='ISA file path')
    
    # Replace command
    replace_parser = subparsers.add_parser('replace', help='Replace a single file in ISA')
    replace_parser.add_argument('isa_file', help='ISA file path')
    replace_parser.add_argument('filename', help='Filename in ISA')
    replace_parser.add_argument('new_file', help='New file path')
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Extract a single file from ISA')
    get_parser.add_argument('isa_file', help='ISA file path')
    get_parser.add_argument('filename', help='Filename in ISA')
    get_parser.add_argument('-o', '--output', default=None, help='Output file path (default: same as filename)')
    
    args = parser.parse_args()
    
    if args.command == 'extract':
        extract_isa(args.isa_file, args.output)
    elif args.command == 'create':
        create_isa(args.input_dir, args.output)
    elif args.command == 'list':
        list_isa(args.isa_file)
    elif args.command == 'replace':
        replace_file_in_isa(args.isa_file, args.filename, args.new_file)
    elif args.command == 'get':
        output = args.output if args.output else args.filename
        extract_single_file(args.isa_file, args.filename, output)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
