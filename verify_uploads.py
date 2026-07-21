import pathlib
import sys
import zipfile
from io import BytesIO

root = pathlib.Path(r'C:/Users/pc/Documents/AI_Document_summarizer')
sys.path.insert(0, str(root))

from utils import extract_text_from_file

plain = extract_text_from_file('sample.txt', b'Plain text upload works')
print('PLAIN_OK:', plain)

xml_payload = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body><w:p><w:r><w:t>Sample DOCX content</w:t></w:r></w:p></w:body>
</w:document>'''

buffer = BytesIO()
with zipfile.ZipFile(buffer, 'w') as archive:
    archive.writestr('word/document.xml', xml_payload)

docx_text = extract_text_from_file('sample.docx', buffer.getvalue())
print('DOCX_OK:', docx_text)
