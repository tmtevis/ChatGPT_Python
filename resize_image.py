from io import BytesIO
from PIL import Image

# Read the image file from disk and resize it
fileName = input("Enter File (with Path) to Resize: ")
width = input("Enter Width: ")
height = input("Enter Height: ")
image = Image.open(fileName)
# width, height = 256, 256
image = image.resize((int(width), int(height)))

# Convert the image to a BytesIO object
byte_stream = BytesIO()
image.save(byte_stream, format='PNG')
byte_array = byte_stream.getvalue()

# response = openai.Image.create_variation(
#   image=byte_array,
#   n=1,
#   size="1024x1024"
# )