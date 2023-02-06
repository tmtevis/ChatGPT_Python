import runway
from runway.data_types import category, vector, image
from your_image_generation_model import big_model, little_model

# The setup() function runs once when the model is initialized, and will run
# again for each well formed HTTP POST request to http://localhost:9000/setup.
@runway.setup(options={'model_size': category(choices=['big', 'little'])})
def setup(opts):
    if opts['model_size'] == 'big':
        return big_model()
    else:
        return little_model()

inputs = { 'noise_vector': vector(length=128, description='A random seed.') }
outputs = { 'image': image(width=512, height=512) }

# The @runway.command() decorator is used to create interfaces to call functions
# remotely via an HTTP endpoint. This lets you send data to, or get data from,
# your model. Each command creates an HTTP route that the Runway app will use
# to communicate with your model (e.g. POST /generate). Multiple commands
# can be defined for the same model.
@runway.command('generate', inputs=inputs, outputs=outputs, description='Generate an image.')
def generate(model, input_args):
    # Functions wrapped by @runway.command() receive two arguments:
    # 1. Whatever is returned by a function wrapped by @runway.setup(),
    #    usually a model.
    # 2. The input arguments sent by the remote caller via HTTP. These values
    #    match the schema defined by inputs.
    img = input_args['image']
    return model.generate(img)

# The runway.run() function triggers a call to the function wrapped by
# @runway.setup() passing model_options as its single argument. It also
# creates an HTTP server that listens for and fulfills remote requests that
# trigger commands.
if __name__ == '__main__':
    runway.run(host='0.0.0.0', port=9000, model_options={ 'model_size': 'big' })