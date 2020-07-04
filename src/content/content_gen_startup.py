from src.content.content_gen import ContentGeneration

try:
    # Use Pil to generate Images
    # Files are loaded, modified, then saved
    from src.content.pillow_content_gen import ImageContentGenerator
except ImportError:
    # Fallback to standard web browser image support
    # Files are copied directly
    from src.content.raw_image_content_gen import ImageContentGenerator

from src.content.pdf2image_content_gen import DocumentContentGenerator


# This doesn't have to be here, but its cleaner here
def initialize_content_gen(**kwargs):
    # Image Support
    ContentGeneration.register_generator(ImageContentGenerator.get_supported_types(), ImageContentGenerator())

    ContentGeneration.register_generator(DocumentContentGenerator.get_supported_types(), DocumentContentGenerator())
