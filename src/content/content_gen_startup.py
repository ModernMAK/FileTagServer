from src.content.content_gen import ContentGeneration

# Use Pillow, pdf2Image, and Unoconv to generate most file previews
# Exclusively requires PIL
from src.content.gen.pillow_content_gen import ImageContentGenerator
# Requires PIL and pdf2Image (Poppler)
from src.content.gen.pdf2image_content_gen import DocumentContentGenerator
# Requires PIL and pdf2Image (Poppler) and Unoconv (LibreOffice/OpenOffice/Other Uno Support)
from src.content.gen.soffice_content_gen import LibreOfficeContentGenerator
# No Requirements
from src.content.raw_image_content_gen import ImageContentGenerator as RawImageContentGenerator


# This doesn't have to be here, but its cleaner here
def initialize_content_gen(**kwargs):

    # Image Support
    ContentGeneration.register_generator(
        ImageContentGenerator.get_supported_types(),
        ImageContentGenerator(),
        False
    )
    # SVG - Support
    ContentGeneration.register_generator(
        RawImageContentGenerator.get_supported_types(),
        RawImageContentGenerator(),
        False
    )
    # Pdf / AI support
    ContentGeneration.register_generator(
        DocumentContentGenerator.get_supported_types(),
        DocumentContentGenerator(),
        False
    )
    # Most Office-Like file support
    ContentGeneration.register_generator(
        LibreOfficeContentGenerator.get_supported_types(),
        LibreOfficeContentGenerator(),
        False
    )
