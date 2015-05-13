import numpy as np
import scipy.signal

# TODO: Add PoolLayer
# TODO: Add DropoutLayer
# TODO: Add a more activation functions

class Layer(object):
	""" Abstract class of a layer. """
	# TODO: Add a gradient checking method

	def __init__(self, input_shape):
		self.input_shape = input_shape
		self.output_shape = input_shape # Most layers don't change the shape
		self.acts = None
		self.gradient = None

	def forward(self, inputs, keepacts=False):
		assert inputs.shape[1:] == self.input_shape[1:], 'Wrong input shape'
		return self._forward(inputs, keepacts)

	def backward(self, gradient, keepgrad=True):
		assert self.acts != [], "No activation values stored, backprop not possible"
		return self._backward(gradient, keepgrad)

	def update_parameters(self, learn_rate, regu_strength):
		""" To be implemented in child class (if needed). """
		pass

	def _forward(self, inputs, keepacts):
		""" To be implemented in child class. """
		raise NotImplementedError

	def _backward(self, gradient, keepgrad):
		""" To be implemented in child class. """
		raise NotImplementedError


class ConvLayer(Layer):
	""" A convolutional layer. """

	def __init__(self, input_shape,	n_filters, field=3):
		""" input_shape is expected to be (num_data, num_chan, x_rez, y_rez).
		"""
		super(ConvLayer, self).__init__(input_shape)
		self.input_channels = input_shape[1]
		# Hyperparameters
		self.n_filters = n_filters
		self.field = field
		 # Parameters
		self.weights = np.random.randn(n_filters, self.input_channels,\
				field, field)
		for i in xrange(n_filters):
			self.weights[i] *= np.sqrt(2.0 / np.sum(self.weights[i].shape))
		self.output_shape = (1, self.n_filters,\
				input_shape[2], input_shape[3])

	def _forward(self, inputs, keepacts=False):
		""" Uses scipy to convolve each channel of each image separately
			which is painfully slow. """
		self.inputs =  inputs
		outputs = np.zeros((inputs.shape[0],) + self.output_shape[1:])
		for n in xrange(inputs.shape[0]): # for each image
			for k in xrange(self.n_filters): # for each kernel
				for c in xrange(inputs.shape[1]): # for each channel
					outputs[n][k] += scipy.signal.convolve2d(inputs[n][c],\
							self.weights[k][c], mode='same')
		if keepacts:
			self.acts = outputs
		return outputs


	def _backward(self, gradient, keepgrad=True):
		""" The slowest backprop you will ever see for a convolutional
			layer. """
		self.gradient = np.zeros(self.weights.shape)
		grad = np.zeros(self.inputs.shape)
		for k in xrange(self.n_filters): # for each kernel
			for c in xrange(self.inputs.shape[1]): # for each channel
				for n in xrange(self.inputs.shape[0]): # for each image
					self.gradient[k][c] += scipy.signal.convolve2d(\
							self.inputs[n][c], gradient[n][k], 'valid')
					grad[n][c] += scipy.signal.correlate2d(gradient[n][k],\
							self.weights[k][c], 'same')
		return grad

	def update_parameters(self, learn_rate, regu_strength):
		self.weights *= (1 - regu_strength)
		self.weights -= self.gradient * learn_rate / len(self.gradient)


class ReLuLayer(Layer):

	def _forward(self, inputs, keepacts=False):
		acts = np.maximum(0, inputs)
		if keepacts:
			self.acts = acts
		return acts

	def _backward(self, gradient, keepgrad=True):
		grad = gradient * (self.acts > 0)
		if keepgrad:
			self.gradient = grad
		return grad


class BiasLayer(Layer):

	def __init__(self, input_shape):
		super(BiasLayer, self).__init__(input_shape)
		self.biases = np.zeros(input_shape[1:])

	def _forward(self, inputs, keepacts=False):
		acts = inputs + self.biases
		if keepacts:
			self.acts = acts
		return acts

	def _backward(self, gradient, keepgrad=True):
		if keepgrad:
			self.gradient = gradient
		return gradient

	def update_parameters(self, learn_rate, regu_strength):
		self.biases -= learn_rate * np.mean(self.gradient, axis=0)


class FCLayer(Layer):

	def __init__(self, input_shape, n_neurons):
		""" input_shape is expected to be (N, C, X, X) """
		super(FCLayer, self).__init__(input_shape)
		n_input = np.prod(input_shape[1:])
		self.weights = np.random.randn(n_input, n_neurons)
		self.weights *= np.sqrt(2.0 / n_input)
		self.output_shape = (input_shape, n_neurons)

	def _forward(self, inputs, keepacts=False):
		inputs = inputs.reshape(inputs.shape[0], np.prod(self.input_shape[1:]))
		self.inputs = inputs # FIXME: This shouldn't be there as such
		acts = np.dot(inputs, self.weights)
		if keepacts:
			self.acts = acts
		return acts

	def _backward(self, gradient, keepgrad=True):
		grad = np.dot(self.inputs.T, gradient)
		if keepgrad:
			self.gradient = grad
		return np.dot(gradient, self.weights.T).reshape((gradient.shape[0],)\
				+ self.input_shape[1:])

	def update_parameters(self, learn_rate, regu_strength):
		self.weights *= (1 - regu_strength)
		self.weights -= self.gradient * learn_rate / len(self.gradient)

