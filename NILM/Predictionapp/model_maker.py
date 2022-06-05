import tensorflow as tf
from tensorflow import keras
import os

class wavenet_Unit(tf.keras.layers.Layer):
    def __init__(self, out_channels, kernel_size, dilation_rate, causal=True, residual = True, **kwargs):
        super(wavenet_Unit, self).__init__(**kwargs)
        self.causal = causal
        self.dilation_rate = dilation_rate
        self.kernel_size = kernel_size
        self.out_channels = out_channels
        self.conv1 = tf.keras.layers.Conv1D(out_channels*2, kernel_size, padding='causal' if causal else 'same', dilation_rate=dilation_rate, activation='tanh')
        self.conv2 = tf.keras.layers.Conv1D(out_channels*2, kernel_size, padding='causal' if causal else 'same', dilation_rate=dilation_rate, activation='sigmoid')
        self.out = tf.keras.layers.Conv1D(out_channels, 1, padding='causal' if causal else 'same')
        self.norm = tf.keras.layers.BatchNormalization()
        self.residual = residual

    def call(self, inputs, training=None, mask=None):
        ## Normalized the input
        ## Passed separetely to tanh and sigmoid parallely.
        norm_inputs = self.norm(inputs)
        tanh = self.conv1(norm_inputs)
        sigmoid = self.conv2(norm_inputs)
        ## Multiply both features
        x = keras.layers.Multiply()([tanh, sigmoid])
        
        ##Pass it through a conv layer
        x = self.out(x)
        without_res = x
        if self.residual:
          x = keras.layers.Add()([x,inputs])
        return x, without_res
        # return x

    def get_config(self):
        config = super(wavenet_Unit, self).get_config()
        config.update({
            'causal': self.causal,
            'dilation_rate': self.dilation_rate,
            'kernel_size': self.kernel_size,
            'out_channels': self.out_channels})
        return config

class wavenet(tf.keras.Model):
  def __init__(self, n_layers = 10, out_channels = 256, kernel_size = 2, dialtion_base = 2, causal = True, base_activation = 'softmax', middle_layers_activation = 'softplus', bias_initializer = None, **kwargs) -> None:
      super(wavenet, self).__init__(**kwargs)
      self.wavenet_layers = [wavenet_Unit(out_channels=out_channels, kernel_size=kernel_size, dilation_rate=dialtion_base**i, causal=causal) for i in range(n_layers)]

      self.bottom = keras.Sequential([           
        keras.layers.Activation(middle_layers_activation),
        keras.layers.BatchNormalization(),
        keras.layers.Dense(out_channels//2, activation= middle_layers_activation),
        keras.layers.Dense(out_channels//4, activation= middle_layers_activation),
        keras.layers.BatchNormalization(),
        keras.layers.Dense(1, activation=base_activation, bias_initializer=bias_initializer) 
      ])
  
  def call(self, inps):
    skip_value = 0
    for layer in self.wavenet_layers:
      inps, single_skip_value = layer(inps)
      skip_value += single_skip_value
    return self.bottom(skip_value)

class wavenet_maker:

    def __init__(self, depth = 16, n_layers = 6, kernel_size = 3, dilation_size = None, middle_layers_activation = 'relu', power_on_z_score = 0):
        self.depth = depth
        self.n_layers = n_layers
        self.kernel_size = kernel_size
        self.dilation_size = dilation_size
        self.middle_layers_activation = middle_layers_activation
        self.power_on_z_score = power_on_z_score
        
    def get_current_address(self):
        return os.getcwd()
    
    def make(self, appliance):
        mirrored_strategy = tf.distribute.MirroredStrategy()
        if self.dilation_size is None:
            self.dilation_size = self.kernel_size
        with mirrored_strategy.scope():

            aggregate_input = tf.keras.Input((None,3),name='aggregate_input')
            
            ## Regression Model is a wevenet model but without Causal Padding nor SE; The Last layer activations is relut to limit the ouput to positive.
            regression_model = wavenet(
                n_layers = self.n_layers,
                kernel_size = self.kernel_size,
                dialtion_base = self.dilation_size,
                out_channels = self.depth,
                causal = False,
                base_activation = 'relu',
                middle_layers_activation = self.middle_layers_activation,
                name = 'regression_model')

            ## Classification Model is a wavenet model but without Causal Padding nor SE; The last layer activation is sigmoid to get binary probabilistic output.
            classification_model = wavenet(        
                n_layers = self.n_layers,
                kernel_size = self.kernel_size,
                dialtion_base = self.dilation_size,
                out_channels = self.depth,
                causal = False,
                base_activation = 'sigmoid',
                middle_layers_activation = self.middle_layers_activation,
                name = 'classification_model')

            ONOFF = classification_model(keras.layers.Dense(self.depth)(aggregate_input))


            ## The Classification output is concatenated with initial aggregate input to be feeded to regression model
            concatenate_list = [ONOFF,aggregate_input]
            power_input = keras.layers.Concatenate()(concatenate_list)

            ## Small model to increase the dimmension of the regression input

            power_input = keras.Sequential([
                                            keras.layers.Conv1D(self.depth//2, 2, padding='same'),
                                            keras.layers.Conv1D(self.depth, 2, padding='same')
            ], name='Depth_Increase')(power_input)

            power = regression_model(power_input)
            # optimizer = tf.keras.optimizers.SGD(0.1)
            main_model = tf.keras.Model(inputs=aggregate_input,outputs=[power,ONOFF])
            main_model.load_weights(f'{self.get_current_address()}\\Predictionapp\\DL\\{appliance.username}\\{appliance.appliance_Name}.h5')
            return tf.function(main_model)