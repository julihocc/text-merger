import sys
import os
import zipfile
import argparse
import tempfile
import shutil
import subprocess
from pathlib import Path

def get_conversion_tool(extension):
    """
    Returns the tool and arguments to convert the file to markdown.
    """
    extension = extension.lower()
    
    # Jupytext for notebooks
    if extension == '.ipynb':
        # Check if jupytext is installed in current python environment
        try:
            subprocess.run([sys.executable, '-m', 'jupytext', '--version'], 
                         capture_output=True, check=True)
            return [sys.executable, '-m', 'jupytext', '--to', 'markdown', '--output', '-']
        except subprocess.CalledProcessError:
            pass
            
    # Pandoc for other formats
    # List of formats pandoc can typically read
    pandoc_formats = {
        '.docx', '.odt', '.tex', '.latex', '.rst', '.org', '.wiki', 
        '.epub', '.html', '.htm'
    }
    
    if extension in pandoc_formats:
        if shutil.which('pandoc'):
            return ['pandoc', '-t', 'markdown']
            
    return None

def convert_file(file_path):
    """
    Attempts to convert a file to markdown using available tools.
    Returns (content, was_converted)
    """
    tool_cmd = get_conversion_tool(Path(file_path).suffix)
    
    if tool_cmd:
        try:
            # For jupytext, we might need to pass the file path as argument if not using stdin/stdout
            # But jupytext --to markdown --output - <file> works or jupytext --to markdown --output - file
            
            cmd = tool_cmd + [str(file_path)]
            
            # Special handling if needed, but simple subprocess should work
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                check=True
            )
            return result.stdout, True
        except subprocess.CalledProcessError as e:
            print(f"Conversion failed for {file_path}: {e}")
            return None, False
        except Exception as e:
            print(f"Error converting {file_path}: {e}")
            return None, False
            
    return None, False

def is_text_file(file_path):
    """
    Check if a file is a text file based on extension or content.
    """
    # Common text extensions
    text_extensions = {
        '.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', 
        '.yml', '.yaml', '.ini', '.conf', '.sh', '.bat', '.c', '.cpp', 
        '.h', '.java', '.rs', '.go', '.ts', '.tsx', '.jsx', '.vue', 
        '.php', '.rb', '.pl', '.sql', '.r', '.m', '.swift', '.kt'
    }
    
    if Path(file_path).suffix.lower() in text_extensions:
        return True
        
    # Heuristic: Try reading the first few bytes
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)
            return True
    except (UnicodeDecodeError, OSError):
        return False

def process_zip(zip_path):
    zip_path = Path(zip_path).resolve()
    if not zip_path.exists():
        print(f"Error: File {zip_path} not found.")
        return

    output_file = zip_path.with_name(f"{zip_path.name}.md")
    
    print(f"Processing {zip_path}...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
        except zipfile.BadZipFile:
            print("Error: Invalid zip file.")
            return

        with open(output_file, 'w', encoding='utf-8') as outfile:
            outfile.write(f"# Content of {zip_path.name}\n\n")
            
            # Walk through the extracted files
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(temp_dir)
                    
                    # Try conversion first
                    content, converted = convert_file(file_path)
                    
                    if converted:
                        outfile.write(f"## File: {relative_path} (Converted)\n")
                        outfile.write(f"- **Size**: {file_path.stat().st_size} bytes\n")
                        outfile.write(f"- **Extension**: {file_path.suffix}\n")
                        outfile.write(f"- **Path**: {relative_path}\n\n")
                        outfile.write("```markdown\n")
                        outfile.write(content)
                        outfile.write("\n```\n\n")
                        outfile.write("---\n\n")
                        print(f"Converted and Added: {relative_path}")
                        continue

                    if is_text_file(file_path):
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='replace') as infile:
                                content = infile.read()
                                
                            outfile.write(f"## File: {relative_path}\n")
                            outfile.write(f"- **Size**: {file_path.stat().st_size} bytes\n")
                            outfile.write(f"- **Extension**: {file_path.suffix}\n")
                            outfile.write(f"- **Path**: {relative_path}\n\n")
                            outfile.write("```\n")
                            outfile.write(content)
                            outfile.write("\n```\n\n")
                            outfile.write("---\n\n")
                            print(f"Added: {relative_path}")
                        except Exception as e:
                            print(f"Skipping {relative_path}: {e}")
    
    print(f"Done! Output saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract text files from a zip and merge into a markdown file.")
    parser.add_argument("zip_file", help="Path to the zip file")
    args = parser.parse_args()
    
    process_zip(args.zip_file)
