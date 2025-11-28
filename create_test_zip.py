import zipfile
import os

def create_dummy_zip(filename="test_archive.zip"):
    with zipfile.ZipFile(filename, 'w') as zf:
        # Text file
        zf.writestr("hello.txt", "Hello world from a text file!")
        
        # Python file
        zf.writestr("script.py", "print('This is a python script')")
        
        # Markdown file in subdirectory
        zf.writestr("docs/readme.md", "# Documentation\nThis is a markdown file.")
        
        # Binary file (dummy png header)
        zf.writestr("image.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
        
    print(f"Created {filename}")

if __name__ == "__main__":
    create_dummy_zip()
