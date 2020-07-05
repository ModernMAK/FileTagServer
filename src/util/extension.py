# A helper for storing extension groups
# Since files can have multiple formats for roughly the same file, (JPEG for instance)
# I wanted to have one 'include-like' operation per file type
# This could then be expanded in other more specific application-based extension support


PNG = 'png'
JPEG_FAMILY = 'jpeg', 'jpg'
JPEG = JPEG_FAMILY
BMP = 'bmp'
GIF = 'gif'
PSD = 'psd'
PSB = 'psb'
TIF = 'tif'
PDF = 'pdf'
RTF = 'rtf'
TXT = 'txt'


# An example of more application based support
ODS = 'ods'
ODT = 'odt'
# Word Doc file types
M_DOC_FAMILY = 'docx', 'docm', 'doc', 'dot', 'dotm', 'dotx'
# Supported
M_WORD = M_DOC_FAMILY, ODT
# Consistency with OD_TEXT
M_TEXT = M_WORD
M_SS = 'csv', 'dbf', 'dif', 'ods'
M_EXCEL = M_SS
OD_TEXT = 'odt'
OD_SS = 'ods'

